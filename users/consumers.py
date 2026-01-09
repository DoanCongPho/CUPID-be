import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Chat, Message, Match
from .token_auth import ExpiringTokenAuthentication

User = get_user_model()

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_chat_if_participant(chat_id, user):
    try:
        chat = Chat.objects.get(pk=chat_id)
    except Chat.DoesNotExist:
        return None
    if chat.match.user1_id == user.id or chat.match.user2_id == user.id:
        return chat
    return None

# run token lookup in sync context to safely access related user
@database_sync_to_async
def get_user_for_token(token):
    from .models import ExpiringToken
    tok = ExpiringToken.verify_token(token)
    if not tok:
        return None
    return tok.user

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # token auth from querystring ?token=<token>
        token = None
        qs = self.scope.get("query_string", b"").decode()
        logger.debug("WS connect: raw query_string=%r", qs)
        if qs:
            for part in qs.split("&"):
                if part.startswith("token="):
                    from urllib.parse import unquote_plus
                    token = unquote_plus(part.split("=", 1)[1])
                    break

        logger.debug("WS connect: extracted token present=%s", bool(token))

        if not token:
            logger.warning("WS connect: no token provided, rejecting (4001)")
            await self.close(code=4001)
            return

        # Verify token and obtain user in sync context
        try:
            user = await get_user_for_token(token)
            logger.debug("WS connect: get_user_for_token returned user=%r", getattr(user, 'id', None))
            if not user:
                logger.warning("WS connect: token invalid/expired - rejecting (4003)")
                await self.close(code=4003)
                return
            logger.info("WS connect: authenticated user id=%s", getattr(user, 'id', None))
        except Exception:
            logger.exception("WS connect: error while resolving token to user")
            await self.close(code=4003)
            return

        # attach user to scope for later use
        self.scope["user"] = user

        chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        logger.debug("WS connect: checking participant membership for chat_id=%s user_id=%s", chat_id, user.id)
        chat = await get_chat_if_participant(chat_id, user)
        if not chat:
            logger.warning("WS connect: user %s is not a participant of chat %s - rejecting (4004)", user.id, chat_id)
            await self.close(code=4004)
            return

        self.chat_group_name = f"chat_{chat_id}"
        try:
            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        except Exception as e:
            logger.exception("WS connect: failed to add to channel layer group: %s", e)
            # If channel layer failed (e.g., Redis unreachable) close with server error
            await self.close(code=1011)
            return

        await self.accept()
        logger.debug("WS connect: accepted and added to group %s", getattr(self, 'chat_group_name', None))

    async def disconnect(self, close_code):
        logger.debug("WS disconnect: close_code=%s for group=%s", close_code, getattr(self, 'chat_group_name', None))
        try:
            await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        except Exception:
            logger.exception("WS disconnect: error while discarding from group")

    async def receive_json(self, content):
        # expected: {"type": "message", "text": "..."}
        try:
            user = self.scope.get("user")
            if not user or user.is_anonymous:
                await self.send_json({"error": "unauthenticated"})
                return

            msg_type = content.get("type")
            if msg_type == "message":
                text = content.get("text")
                chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
                # save message
                msg = await database_sync_to_async(Message.objects.create)(chat_id=chat_id, sender=user, content=text)
                payload = {
                    "id": msg.id,
                    "chat_id": chat_id,
                    "sender": {"id": user.id, "email": getattr(user, "email", None)},
                    "content": msg.content,
                    "sent_at": msg.sent_at.isoformat(),
                }
                try:
                    await self.channel_layer.group_send(self.chat_group_name, {"type": "chat.message", "message": payload})
                except Exception as e:
                    logger.exception("WS receive_json: failed to group_send: %s", e)
                    # still attempt to send back an error to client
                    await self.send_json({"error": "server_error", "detail": str(e)})
        except Exception as e:
            logger.exception("WS receive_json: unexpected error: %s", e)
            try:
                await self.send_json({"error": "server_error", "detail": str(e)})
            except Exception:
                logger.exception("WS receive_json: failed to send error to client")

    async def chat_message(self, event):
        message = event["message"]
        await self.send_json({"type": "message", "data": message})
