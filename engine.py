import os
import json
import numpy as np
from datetime import datetime
from scipy.optimize import linear_sum_assignment
from users.models.preference import Preference, UserPreference
from users.models.profile import UserProfile
from django.contrib.auth import get_user_model

# --- Configuration ---
DATA_DIR = "data_json"
VECTOR_DIM = None  # set once preferences are loaded
LEARNING_RATE = 0.1  # alpha: how fast a vector drifts per interaction


class DatingEngine:
    def __init__(self):
        # users are held in memory; this stands in for a database
        self.users_db = {}
        self.interactions = []
        self.interests_pool = self._load_interests_pool()
        global VECTOR_DIM
        VECTOR_DIM = 1 + len(self.interests_pool)

    def _load_interests_pool(self):
        return list(Preference.objects.order_by('name').values_list('name', flat=True))

    # --- 1. Feature engineering ---
    def _create_initial_vector(self, profile, user_id=None):
        """
        Turn a raw UserProfile into a numpy vector.

        Layout: [normalised_age, one_hot_interest_0, one_hot_interest_1, ...]
        """
        # age, normalised to 0-1 over an assumed range of 15 to 45
        if hasattr(profile, 'date_of_birth') and profile.date_of_birth:
            current_year = datetime.now().year
            age = current_year - profile.date_of_birth.year
        else:
            age = 25  # default
        norm_age = (age - 15) / (45 - 15)
        norm_age = np.clip(norm_age, 0.0, 1.0)

        # interests, one-hot encoded against the shared pool
        interests_vec = [0.0] * len(self.interests_pool)
        if user_id:
            user_pref_names = set(UserPreference.objects.filter(user_id=user_id).select_related('preference').values_list('preference__name', flat=True))
        else:
            user_pref_names = set(getattr(profile, 'interests', []) or [])
        for idx, interest in enumerate(self.interests_pool):
            if interest in user_pref_names:
                interests_vec[idx] = 1.0
        final_vec = np.array([norm_age] + interests_vec, dtype=np.float32)
        return final_vec

    # --- 2. Load data ---
    def load_data_from_json(self):
        print("--- Loading data from JSON into the engine ---")
        if not os.path.exists(DATA_DIR):
            print(f"Error: directory not found: {DATA_DIR}")
            return

        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]

        for f_name in files:
            path = os.path.join(DATA_DIR, f_name)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                user_id = data['user_id']
                embedding = self._create_initial_vector(data)

                self.users_db[user_id] = {
                    "info": data,
                    "vector": embedding
                }

                # flatten every user's ratings into one list for training
                for rating in data.get('ratings', []):
                    self.interactions.append({
                        "user_id": user_id,
                        "target_id": rating['target_user_id'],
                        "score": rating['score'],
                        "timestamp": rating.get('timestamp', 0)
                    })

        print(f"Loaded {len(self.users_db)} users and {len(self.interactions)} ratings.")

    # --- 3. Vector drift: learning from interactions ---
    def run_training_update(self):
        """
        Replay the rating history to nudge each user's vector.
        """
        print("--- Running vector update (training) ---")

        # oldest first, so preferences evolve in the order they actually did
        sorted_interactions = sorted(self.interactions, key=lambda x: x['timestamp'])

        for interaction in sorted_interactions:
            u_id = interaction['user_id']
            t_id = interaction['target_id']
            score = interaction['score']  # 1 to 5

            if u_id not in self.users_db or t_id not in self.users_db:
                continue

            vec_user = self.users_db[u_id]['vector']
            vec_target = self.users_db[t_id]['vector']

            # map the 1-5 score onto -1.0 (dislike) .. 0.0 (neutral) .. 1.0 (like)
            normalized_score = (score - 3) / 2.0

            # drift:  new = old + LR * score * (target - old)
            #   score > 0 pulls the user towards the target
            #   score < 0 pushes the user away from it
            delta = vec_target - vec_user
            update_step = LEARNING_RATE * normalized_score * delta

            self.users_db[u_id]['vector'] += update_step

        print("Preference vectors updated for all users.")

    # --- 3.1. Exporting vectors ---
    def save_vectors_to_json(self, filename="embeddings.json"):
        """Write every user's embedding vector to a JSON file."""
        output = {}
        for user_id, user_data in self.users_db.items():
            output[f"user_{user_id}"] = {
                "user_id": user_id,
                "gender": user_data['info']['gender'],
                "year_of_birth": user_data['info']['year_of_birth'],
                "interests": user_data['info']['interests'],
                "embedding_vector": user_data['vector'].tolist()
            }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved embedding vectors to: {filename}")

    def save_vectors_to_txt(self, filename="embeddings.txt"):
        """
        Write every user's embedding vector to a plain-text report.
        Format: user_id | gender | year_of_birth | interests | vector
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("EMBEDDING VECTORS\n")
            f.write("=" * 100 + "\n\n")

            for user_id, user_data in self.users_db.items():
                f.write(f"User ID: {user_id}\n")
                f.write(f"Gender: {user_data['info']['gender']}\n")
                f.write(f"Year of Birth: {user_data['info']['year_of_birth']}\n")
                f.write(f"Interests: {', '.join(user_data['info']['interests'])}\n")
                f.write(f"Embedding Vector ({len(user_data['vector'])} dimensions):\n")
                f.write(f"  {user_data['vector'].tolist()}\n")
                f.write("-" * 100 + "\n\n")

        print(f"Saved embedding vectors to: {filename}")

    # --- 4. Scoring and recommendations ---
    def _cosine_similarity(self, vec_a, vec_b):
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def get_recommendations(self, user_id, top_k=5):
        if user_id not in self.users_db:
            return []

        current_user = self.users_db[user_id]
        my_vector = current_user['vector']
        my_gender = current_user['info']['gender']

        candidates = []

        for other_id, other_data in self.users_db.items():
            if other_id == user_id:
                continue

            # bipartite matching: only consider the opposite gender
            if other_data['info']['gender'] == my_gender:
                continue

            # note: already-rated users are deliberately not filtered out here,
            # so the demo can show how their scores move after training

            similarity = self._cosine_similarity(my_vector, other_data['vector'])

            candidates.append({
                "user_id": other_id,
                "gender": other_data['info']['gender'],
                "interests": other_data['info']['interests'],
                "match_score": float(similarity)
            })

        candidates.sort(key=lambda x: x['match_score'], reverse=True)

        return candidates[:top_k]

    # --- 5. Hungarian algorithm: globally optimal pairing ---
    def find_optimal_pairs(self):
        """
        Use the Hungarian (Munkres) algorithm to pair males with females so
        that the total similarity across all pairs is maximised.

        Returns:
            (list of pair dicts, total similarity score)
        """
        print("\n--- Computing optimal pairs with the Hungarian algorithm ---")

        males = []
        females = []

        for user_id, user_data in self.users_db.items():
            if user_data['info']['gender'] == 'M':
                males.append(user_id)
            else:
                females.append(user_id)

        print(f"Males: {len(males)}, Females: {len(females)}")

        if len(males) == 0 or len(females) == 0:
            print("Not enough of both genders to form pairs.")
            return []

        similarity_matrix = np.zeros((len(males), len(females)))

        for i, male_id in enumerate(males):
            male_vector = self.users_db[male_id]['vector']
            for j, female_id in enumerate(females):
                female_vector = self.users_db[female_id]['vector']
                similarity = self._cosine_similarity(male_vector, female_vector)
                similarity_matrix[i, j] = similarity

        # linear_sum_assignment minimises, so negate to turn this into a
        # maximisation problem
        cost_matrix = -similarity_matrix

        row_indices, col_indices = linear_sum_assignment(cost_matrix)

        optimal_pairs = []
        total_score = 0.0

        for i, j in zip(row_indices, col_indices):
            male_id = males[i]
            female_id = females[j]
            similarity = similarity_matrix[i, j]
            total_score += similarity

            optimal_pairs.append({
                'male_id': male_id,
                'male_info': self.users_db[male_id]['info'],
                'female_id': female_id,
                'female_info': self.users_db[female_id]['info'],
                'similarity_score': float(similarity)
            })

        optimal_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)

        print(f"Found {len(optimal_pairs)} optimal pairs.")
        print(f"Total similarity score: {total_score:.4f}")
        print(f"Average score: {total_score/len(optimal_pairs):.4f}")

        return optimal_pairs, total_score

    def print_optimal_pairs(self, optimal_pairs):
        """Print the optimal pairing result in a readable layout."""
        print("\n" + "=" * 100)
        print("OPTIMAL PAIRS (HUNGARIAN ALGORITHM)")
        print("=" * 100 + "\n")

        for idx, pair in enumerate(optimal_pairs, 1):
            print(f"Pair {idx}: User {pair['male_id']} (M) - User {pair['female_id']} (F)")
            print(f"  Similarity score: {pair['similarity_score']:.4f}")
            print(f"  M - born {pair['male_info']['year_of_birth']}, interests: {', '.join(pair['male_info']['interests'])}")
            print(f"  F - born {pair['female_info']['year_of_birth']}, interests: {', '.join(pair['female_info']['interests'])}")
            print("-" * 100)

    def save_optimal_pairs_to_file(self, optimal_pairs, total_score, filename="optimal_pairs.txt"):
        """Write the optimal pairing result to a plain-text report."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("OPTIMAL PAIRS (HUNGARIAN ALGORITHM)\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Total pairs: {len(optimal_pairs)}\n")
            f.write(f"Total similarity score: {total_score:.4f}\n")
            f.write(f"Average score: {total_score/len(optimal_pairs):.4f}\n\n")
            f.write("=" * 100 + "\n\n")

            for idx, pair in enumerate(optimal_pairs, 1):
                f.write(f"Pair {idx}: User {pair['male_id']} (M) - User {pair['female_id']} (F)\n")
                f.write(f"  Similarity score: {pair['similarity_score']:.4f}\n")
                f.write(f"  M - born {pair['male_info']['year_of_birth']}, interests: {', '.join(pair['male_info']['interests'])}\n")
                f.write(f"  F - born {pair['female_info']['year_of_birth']}, interests: {', '.join(pair['female_info']['interests'])}\n")
                f.write("-" * 100 + "\n\n")

        print(f"Saved pairing result to: {filename}")

    def save_optimal_pairs_to_json(self, optimal_pairs, total_score, filename="optimal_pairs.json"):
        """Write the optimal pairing result to JSON, ids and scores only."""
        output = {
            "total_pairs": len(optimal_pairs),
            "total_similarity_score": round(total_score, 4),
            "average_score": round(total_score / len(optimal_pairs), 4),
            "pairs": []
        }

        for pair in optimal_pairs:
            output["pairs"].append({
                "male_id": pair['male_id'],
                "female_id": pair['female_id'],
                "similarity_score": round(pair['similarity_score'], 4)
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Saved pairing result to JSON: {filename}")


# --- Demo ---
if __name__ == "__main__":
    engine = DatingEngine()
    engine.load_data_from_json()

    print("\n--- Saving vectors BEFORE training ---")
    engine.save_vectors_to_json("embeddings_before.json")
    engine.save_vectors_to_txt("embeddings_before.txt")

    TEST_USER_ID = 0
    print(f"\n=== BEFORE TRAINING (User {TEST_USER_ID}) ===")
    recs_before = engine.get_recommendations(TEST_USER_ID)
    for r in recs_before:
        print(f"User {r['user_id']} ({r['gender']}) - Score: {r['match_score']:.4f} - interests: {r['interests']}")

    engine.run_training_update()

    print("\n--- Saving vectors AFTER training ---")
    engine.save_vectors_to_json("embeddings_after.json")
    engine.save_vectors_to_txt("embeddings_after.txt")

    print(f"\n=== AFTER TRAINING (User {TEST_USER_ID}) ===")
    recs_after = engine.get_recommendations(TEST_USER_ID)
    for r in recs_after:
        print(f"User {r['user_id']} ({r['gender']}) - Score: {r['match_score']:.4f} - interests: {r['interests']}")

    print("\nThe recommendation order should have shifted: users who share interests "
          "with the people User 0 rated 5 stars now score higher.")
    print("\nWrote 4 files: embeddings_before.json, embeddings_before.txt, "
          "embeddings_after.json, embeddings_after.txt")

    print("\n" + "=" * 100)
    print("OPTIMAL PAIRING")
    print("=" * 100)
    optimal_pairs, total_score = engine.find_optimal_pairs()

    engine.print_optimal_pairs(optimal_pairs)

    engine.save_optimal_pairs_to_file(optimal_pairs, total_score, "optimal_pairs.txt")
    engine.save_optimal_pairs_to_json(optimal_pairs, total_score, "optimal_pairs.json")

    print("\nDone. The Hungarian algorithm found the pairing with the highest total score.")
