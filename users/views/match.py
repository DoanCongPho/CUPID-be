"""
Match and Quest views for the users app.
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from ..models import Match, Quests, UserPreference, UserProfile
from ..serializers.match import MatchSerializer, QuestSerializer
from engine import DatingEngine
from engine_gen_quest import gen_quests_for_matches
import json

User = get_user_model()
PLACES_PATH = "places.json"


@extend_schema_view(
    post=extend_schema(
        description="Generate quests for all matches. Only admin or staff should use this endpoint.",
        responses={
            200: OpenApiResponse(
                description="Number of quests created and list of created quests",
                response={
                    "type": "object",
                    "properties": {
                        "created_quests": {"type": "integer"},
                        "quests": {"type": "array", "items": {"type": "object"}}
                    }
                }
            )
        }
    )
)
class GenQuestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from ..models.task import Task
        from datetime import timedelta

        print("[GenQuestView] Start generating quests...")

        # Calculate tomorrow's date
        tomorrow = timezone.now().date() + timedelta(days=1)
        print(f"[GenQuestView] Generating quests for date: {tomorrow}")

        with open(PLACES_PATH, encoding='utf-8') as f:
            places = json.load(f)
        print(f"[GenQuestView] Loaded {len(places)} places.")

        matches = Match.objects.all()
        print(f"[GenQuestView] Found {matches.count()} matches.")

        user_profiles = {p.user_id: p for p in UserProfile.objects.all()}
        print(f"[GenQuestView] Loaded {len(user_profiles)} user profiles.")

        # Get tasks for tomorrow only
        tasks = {}
        tomorrow_start = timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time()))
        tomorrow_end = timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.max.time()))

        all_tasks = Task.objects.filter(
            scheduled_start_time__gte=tomorrow_start,
            scheduled_start_time__lte=tomorrow_end
        )
        print(f"[GenQuestView] Loaded {all_tasks.count()} tasks for {tomorrow}.")

        for t in all_tasks:
            if t.user_id not in tasks:
                tasks[t.user_id] = []
            if t.scheduled_start_time and t.scheduled_end_time:
                tasks[t.user_id].append((
                    t.scheduled_start_time.strftime("%H:%M"),
                    t.scheduled_end_time.strftime("%H:%M")
                ))
        print(f"[GenQuestView] Compiled constraints for {len(tasks)} users.")

        quest_infos = gen_quests_for_matches(matches, user_profiles, tasks, places)
        print(f"[GenQuestView] Generated quest info for {len(quest_infos)} matches.")

        created = 0
        created_quests = []
        for idx, info in enumerate(quest_infos):
            if not info:
                print(f"[GenQuestView] Quest info {idx} is None, skipping.")
                continue
            match = info["match"]
            # Chỉ skip nếu quest cho match và location_name này đã tồn tại
            if Quests.objects.filter(match=match, location_name=info["location_name"]).exists():
                print(f"[GenQuestView] Quest for match {match.id} at {info['location_name']} already exists, skipping.")
                continue
            quest = Quests.objects.create(
                match=match,
                location_name=info["location_name"],
                activity=info["activity"],
                quest_date=tomorrow,  # Set quest date to tomorrow
                location_latitude=info["location_latitude"],
                location_longitude=info["location_longitude"],
                status_user1=Quests.STATUS_PENDING,
                status_user2=Quests.STATUS_PENDING,
                xp_reward=info["xp_reward"],
            )
            created_quests.append({
                "id": quest.id,
                "match_id": match.id,
                "location_name": quest.location_name,
                "activity": quest.activity,
                "quest_date": str(quest.quest_date),
                "location_latitude": quest.location_latitude,
                "location_longitude": quest.location_longitude,
                "status_user1": quest.status_user1,
                "status_user2": quest.status_user2,
                "xp_reward": quest.xp_reward,
                "time_start": info.get("time_start"),
                "time_end": info.get("time_end"),
            })
            print(f"[GenQuestView] Created quest {quest.id} for match {match.id}.")
            created += 1
        print(f"[GenQuestView] Finished. Created {created} quests.")
        return Response({"created_quests": created, "quests": created_quests}, status=200)

@extend_schema_view(
    get=extend_schema(responses=MatchSerializer(many=True)),
    post=extend_schema(request=MatchSerializer, responses=MatchSerializer),
)
class MatchListCreateView(generics.ListCreateAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(user1=user) | Q(user2=user)).order_by("-matched_at")

    def perform_create(self, serializer):
        serializer.save(user1=self.request.user)


@extend_schema_view(
    get=extend_schema(responses=MatchSerializer),
    put=extend_schema(request=MatchSerializer, responses=MatchSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class MatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(user1=user) | Q(user2=user))

    def destroy(self, request, *args, **kwargs):
        """Hard delete the Match row. Ownership is enforced by get_queryset()."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        """Update the Match instance (explicit PUT handler for testing)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(
    request=None,
    responses=MatchSerializer,
    description="Create or return a Match between authenticated user and user_id (PUT).",
)
class MatchWithUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_id):
        # cannot match with self
        if request.user.id == user_id:
            return Response({"detail": "cannot match with yourself"}, status=status.HTTP_400_BAD_REQUEST)
        # ensure target user exists
        target = get_object_or_404(User, pk=user_id)
        # check existing match in either order
        match = Match.objects.filter(
            (Q(user1=request.user) & Q(user2=target)) | (Q(user1=target) & Q(user2=request.user))
        ).first()
        if match:
            serializer = MatchSerializer(match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # create new match with request.user as user1
        match = Match.objects.create(user1=request.user, user2=target, matched_at=timezone.now())
        serializer = MatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(responses=QuestSerializer(many=True)),
    post=extend_schema(request=QuestSerializer, responses=QuestSerializer),
)
class QuestListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # only quests for matches where user is participant
        return Quests.objects.filter(Q(match__user1=user) | Q(match__user2=user)).order_by("-quest_date")

    def perform_create(self, serializer):
        # trust provided match; could add extra validation here
        serializer.save()


@extend_schema_view(
    get=extend_schema(responses=QuestSerializer),
    put=extend_schema(request=QuestSerializer, responses=QuestSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class QuestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Quests.objects.filter(Q(match__user1=user) | Q(match__user2=user))

    def destroy(self, request, *args, **kwargs):
        """Hard delete the Quest row. Ownership is enforced by get_queryset()."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema_view(
    post=extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"hint": {"type": "string"}},
                "required": ["hint"]
            }
        },
        responses=QuestSerializer,
        description="Post a hint for the quest. Authenticated user must be a participant in the match. Updates hint_user1 or hint_user2 depending on user role."
    )
)
class QuestPostHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, pk):
        quest = get_object_or_404(Quests, pk=pk)
        user = request.user
        match = quest.match
        hint = request.data.get("hint", "")
        if not hint:
            return Response({"detail": "Hint is required."}, status=status.HTTP_400_BAD_REQUEST)
        if match.user1 == user:
            quest.hint_user1 = hint
        elif match.user2 == user:
            quest.hint_user2 = hint
        else:
            return Response({"detail": "You are not a participant in this quest's match."}, status=status.HTTP_403_FORBIDDEN)
        quest.save()
        serializer = QuestSerializer(quest)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema_view(
    post=extend_schema(
        request=None,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'quest': {'type': 'object'},
                    'xp_awarded': {'type': 'boolean'},
                    'xp_amount': {'type': 'integer'}
                }
            }
        },
        description="Mark a quest as completed for the authenticated user. If both users complete the quest, XP is awarded and the quest is deleted."
    )
)
class QuestCompleteView(APIView):
    """
    Mark a quest as completed for the authenticated user.
    When both users complete the quest:
    - XP is awarded to both users
    - Quest is deleted
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        quest = get_object_or_404(Quests, pk=pk)
        user = request.user
        match = quest.match

        # Check if user is participant
        if match.user1 != user and match.user2 != user:
            return Response(
                {"detail": "You are not a participant in this quest's match."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update the appropriate user status
        if match.user1 == user:
            if quest.status_user1 == Quests.STATUS_COMPLETED:
                return Response({"detail": "You have already completed this quest."}, status=status.HTTP_400_BAD_REQUEST)
            quest.status_user1 = Quests.STATUS_COMPLETED
        elif match.user2 == user:
            if quest.status_user2 == Quests.STATUS_COMPLETED:
                return Response({"detail": "You have already completed this quest."}, status=status.HTTP_400_BAD_REQUEST)
            quest.status_user2 = Quests.STATUS_COMPLETED

        quest.save()

        # Check if both users have completed the quest
        xp_awarded = False
        xp_amount = 0
        if quest.status_user1 == Quests.STATUS_COMPLETED and quest.status_user2 == Quests.STATUS_COMPLETED:
            # Award XP to both users
            xp_amount = quest.xp_reward or 0
            try:
                profile1 = match.user1.profile
                profile1.total_xp += xp_amount
                profile1.save()
            except UserProfile.DoesNotExist:
                pass

            try:
                profile2 = match.user2.profile
                profile2.total_xp += xp_amount
                profile2.save()
            except UserProfile.DoesNotExist:
                pass

            xp_awarded = True

            # Delete the quest
            # quest_data = QuestSerializer(quest).data
            # quest.delete()

            return Response({
                "message": "Quest completed by both users! XP awarded and quest removed.",
                "quest": serializer.data,
                "xp_awarded": True,
                "xp_amount": xp_amount
            }, status=status.HTTP_200_OK)

        # Only one user has completed so far
        serializer = QuestSerializer(quest)
        return Response({
            "message": "Quest marked as completed. Waiting for your partner to complete.",
            "quest": serializer.data,
            "xp_awarded": False,
            "xp_amount": 0
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"rating": {"type": "integer", "minimum": 1, "maximum": 5}},
                "required": ["rating"]
            }
        },
        responses=MatchSerializer,
        description="Post a rating for the match. Authenticated user must be a participant. Updates user1_rating or user2_rating depending on user role."
    )
)
class MatchRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        user = request.user
        rating = request.data.get("rating")
        if rating is None:
            return Response({"detail": "Rating is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return Response({"detail": "Rating must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        if not (1 <= rating <= 5):
            return Response({"detail": "Rating must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)
        if match.user1 == user:
            match.user1_rating = rating
        elif match.user2 == user:
            match.user2_rating = rating
        else:
            return Response({"detail": "You are not a participant in this match."}, status=status.HTTP_403_FORBIDDEN)
        match.save()
        serializer = MatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema_view(
    post=extend_schema(
        responses={
            "application/json": {
                "type": "object",
                "properties": {
                    "total_pairs": {"type": "integer"},
                    "total_similarity_score": {"type": "number"},
                    "average_score": {"type": "number"},
                    "pairs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "male_id": {"type": "integer"},
                                "female_id": {"type": "integer"},
                                "similarity_score": {"type": "number"}
                            }
                        }
                    }
                }
            }
        },
        description="Match all single users using DatingEngine and return optimal pairs."
    )
)
class SingleUserMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        User = get_user_model()
        matched_user_ids = set()
        for match in Match.objects.all():
            matched_user_ids.add(match.user1_id)
            matched_user_ids.add(match.user2_id)
        single_profiles = UserProfile.objects.exclude(user_id__in=matched_user_ids)
        engine = DatingEngine()
        for profile in single_profiles:
            engine.users_db[profile.user_id] = {
                "info": {
                    "user_id": profile.user_id,
                    "gender": profile.gender,
                    "year_of_birth": profile.date_of_birth.year if profile.date_of_birth else None,
                    "interests": list(UserPreference.objects.filter(user_id=profile.user_id).select_related('preference').values_list('preference__name', flat=True))
                },
                "vector": engine._create_initial_vector(profile, user_id=profile.user_id)
            }
        optimal_pairs, total_score = engine.find_optimal_pairs()
        # Add pairs to Match if similarity_score > 0.5
        created_matches = []
        for pair in optimal_pairs:
            if pair["similarity_score"] > 0.5:
                male_id = pair["male_id"]
                female_id = pair["female_id"]
                # Check if match already exists
                if not Match.objects.filter(user1_id=male_id, user2_id=female_id).exists() and not Match.objects.filter(user1_id=female_id, user2_id=male_id).exists():
                    match = Match.objects.create(
                        user1_id=male_id,
                        user2_id=female_id,
                        status_user1=Match.STATUS_PENDING,
                        status_user2=Match.STATUS_PENDING,
                        matched_at=timezone.now()
                    )
                    created_matches.append(match.id)
                    # Update is_matched for both profiles
                    for uid in [male_id, female_id]:
                        try:
                            profile = UserProfile.objects.get(user_id=uid)
                            profile.is_matched = True
                            profile.save()
                        except UserProfile.DoesNotExist:
                            pass
        response = {
            "total_pairs": len(optimal_pairs),
            "total_similarity_score": round(total_score, 4),
            "average_score": round(total_score / len(optimal_pairs), 4) if optimal_pairs else 0,
            "pairs": [
                {
                    "male_id": pair["male_id"],
                    "female_id": pair["female_id"],
                    "similarity_score": round(pair["similarity_score"], 4)
                } for pair in optimal_pairs
            ],
            "created_matches": created_matches
        }
        return Response(response, status=status.HTTP_200_OK)

@extend_schema_view(
    post=extend_schema(
        request=None,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'match': {'type': 'object'},
                    'both_confirmed': {'type': 'boolean'}
                }
            }
        },
        description="Confirm a match for the authenticated user. When both users confirm, the match is fully completed."
    )
)
class MatchConfirmView(APIView):
    """
    Confirm a match for the authenticated user.
    When both users confirm, the match status becomes fully completed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        user = request.user

        # Check if user is participant
        if match.user1 != user and match.user2 != user:
            return Response(
                {"detail": "You are not a participant in this match."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update the appropriate user status
        if match.user1 == user:
            if match.status_user1 == Match.STATUS_COMPLETED:
                return Response({"detail": "You have already confirmed this match."}, status=status.HTTP_400_BAD_REQUEST)
            match.status_user1 = Match.STATUS_COMPLETED
        elif match.user2 == user:
            if match.status_user2 == Match.STATUS_COMPLETED:
                return Response({"detail": "You have already confirmed this match."}, status=status.HTTP_400_BAD_REQUEST)
            match.status_user2 = Match.STATUS_COMPLETED

        match.save()

        # Check if both users have confirmed
        both_confirmed = (match.status_user1 == Match.STATUS_COMPLETED and
                         match.status_user2 == Match.STATUS_COMPLETED)

        serializer = MatchSerializer(match)

        if both_confirmed:
            return Response({
                "message": "Both users have confirmed the match! Match is now fully completed.",
                "match": serializer.data,
                "both_confirmed": True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Match confirmed. Waiting for your partner to confirm.",
                "match": serializer.data,
                "both_confirmed": False
            }, status=status.HTTP_200_OK)
