import os
import json
import numpy as np
from datetime import datetime
from scipy.optimize import linear_sum_assignment
from users.models.preference import Preference, UserPreference
from users.models.profile import UserProfile
from django.contrib.auth import get_user_model

# --- CẤU HÌNH ---
DATA_DIR = "data_json"
VECTOR_DIM = None  # Will be set after loading preferences
LEARNING_RATE = 0.1 # Tốc độ cập nhật vector (Alpha)

class DatingEngine:
    def __init__(self):
        # Lưu trữ toàn bộ users trong RAM (Mô phỏng Database)
        self.users_db = {}
        self.interactions = []
        self.interests_pool = self._load_interests_pool()
        global VECTOR_DIM
        VECTOR_DIM = 1 + len(self.interests_pool)

    def _load_interests_pool(self):
        # Load all preferences from the database, ordered by name
        return list(Preference.objects.order_by('name').values_list('name', flat=True))

    # --- 1. FEATURE ENGINEERING (TẠO VECTOR) ---
    def _create_initial_vector(self, profile, user_id=None):
        """
        Chuyển thông tin thô (UserProfile) thành Vector Numpy
        """
        # A. Xử lý Tuổi (Chuẩn hóa về 0-1)
        # Giả sử dải tuổi từ 15 đến 45
        if hasattr(profile, 'date_of_birth') and profile.date_of_birth:
            current_year = datetime.now().year
            age = current_year - profile.date_of_birth.year
        else:
            age = 25  # default
        norm_age = (age - 15) / (45 - 15)
        norm_age = np.clip(norm_age, 0.0, 1.0)

        # B. Xử lý Sở thích (One-hot Encoding)
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

    # --- 2. LOAD DATA ---
    def load_data_from_json(self):
        print("--- Đang tải dữ liệu từ JSON vào Engine ---")
        if not os.path.exists(DATA_DIR):
            print(f"Lỗi: Không tìm thấy thư mục {DATA_DIR}")
            return

        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]

        for f_name in files:
            path = os.path.join(DATA_DIR, f_name)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                user_id = data['user_id']

                # Tạo vector ban đầu cho user này
                embedding = self._create_initial_vector(data)

                # Lưu vào "Database" giả lập
                self.users_db[user_id] = {
                    "info": data,          # Thông tin gốc
                    "vector": embedding    # Vector để tính toán
                }

                # Gom rating vào list chung để xử lý
                for rating in data.get('ratings', []):
                    self.interactions.append({
                        "user_id": user_id,
                        "target_id": rating['target_user_id'],
                        "score": rating['score'],
                        "timestamp": rating.get('timestamp', 0)
                    })

        print(f"✅ Đã tải {len(self.users_db)} users và {len(self.interactions)} ratings.")

    # --- 3. CORE AI: VECTOR DRIFT (HỌC TỪ TƯƠNG TÁC) ---
    def run_training_update(self):
        """
        Mô phỏng quá trình học: Duyệt qua lịch sử rating để chỉnh sửa vector
        """
        print("--- Đang chạy cập nhật Vector (Training) ---")

        # Sắp xếp interaction theo thời gian (cũ trước, mới sau)
        # Để mô phỏng đúng quá trình phát triển sở thích
        sorted_interactions = sorted(self.interactions, key=lambda x: x['timestamp'])

        total_loss = 0

        for interaction in sorted_interactions:
            u_id = interaction['user_id']
            t_id = interaction['target_id']
            score = interaction['score'] # 1 đến 5

            # Kiểm tra xem user còn tồn tại không
            if u_id not in self.users_db or t_id not in self.users_db:
                continue

            vec_user = self.users_db[u_id]['vector']
            vec_target = self.users_db[t_id]['vector']

            # --- LOGIC CẬP NHẬT VECTOR ---
            # Chuẩn hóa score: 1->-1.0 (Ghét), 3->0.0 (Bình thường), 5->1.0 (Thích)
            normalized_score = (score - 3) / 2.0

            # Công thức Drift:
            # Vector_User_Mới = Vector_User_Cũ + LR * Score * (Vector_Target - Vector_User_Cũ)
            # Ý nghĩa:
            # - Nếu Score > 0 (Thích): Kéo User về phía Target
            # - Nếu Score < 0 (Ghét): Đẩy User ra xa Target

            delta = vec_target - vec_user
            update_step = LEARNING_RATE * normalized_score * delta

            # Cập nhật
            self.users_db[u_id]['vector'] += update_step

            # (Tùy chọn) Chuẩn hóa lại vector để không bị quá lớn (L2 Norm)
            # norm = np.linalg.norm(self.users_db[u_id]['vector'])
            # if norm > 0: self.users_db[u_id]['vector'] /= norm

        print("✅ Đã cập nhật xong vector sở thích cho tất cả User!")

    # --- 3.1. XUẤT VECTOR RA FILE ---
    def save_vectors_to_json(self, filename="embeddings.json"):
        """
        Lưu tất cả vector embedding của users ra file JSON
        """
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
        print(f"✅ Đã lưu embedding vectors vào file: {filename}")

    def save_vectors_to_txt(self, filename="embeddings.txt"):
        """
        Lưu tất cả vector embedding của users ra file TXT
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

        print(f"✅ Đã lưu embedding vectors vào file: {filename}")

    # --- 4. TÍNH TOÁN & GỢI Ý ---
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

        # Duyệt qua tất cả user khác
        for other_id, other_data in self.users_db.items():
            # 1. Lọc chính mình
            if other_id == user_id: continue

            # 2. Lọc Bipartite (Khác giới tính)
            if other_data['info']['gender'] == my_gender: continue

            # (Tùy chọn) 3. Lọc những người đã từng rate rồi?
            # Ở demo này ta bỏ qua để xem điểm số thay đổi thế nào

            # Tính độ tương đồng
            similarity = self._cosine_similarity(my_vector, other_data['vector'])

            candidates.append({
                "user_id": other_id,
                "gender": other_data['info']['gender'],
                "interests": other_data['info']['interests'], # Để hiển thị cho vui
                "match_score": float(similarity)
            })

        # Sắp xếp giảm dần theo match_score
        candidates.sort(key=lambda x: x['match_score'], reverse=True)

        return candidates[:top_k]

    # --- 5. THUẬT TOÁN HUNGARIAN (GỚI Ý CẶP TỐI ƯU) ---
    def find_optimal_pairs(self):
        """
        Sử dụng thuật toán Hungarian (Munkres) để ghép cặp tối ưu
        giữa nam và nữ sao cho tổng điểm tương đồng là lớn nhất

        Returns:
            List of tuples: [(male_id, female_id, similarity_score), ...]
        """
        print("\n--- Đang tính toán ghép cặp tối ưu bằng thuật toán Hungarian ---")

        # Phân chia users theo giới tính
        males = []
        females = []

        for user_id, user_data in self.users_db.items():
            if user_data['info']['gender'] == 'M':
                males.append(user_id)
            else:
                females.append(user_id)

        print(f"Số nam: {len(males)}, Số nữ: {len(females)}")

        if len(males) == 0 or len(females) == 0:
            print("⚠️ Không đủ cả hai giới để ghép cặp!")
            return []

        # Tạo ma trận điểm tương đồng (similarity matrix)
        # Kích thước: len(males) x len(females)
        similarity_matrix = np.zeros((len(males), len(females)))

        for i, male_id in enumerate(males):
            male_vector = self.users_db[male_id]['vector']
            for j, female_id in enumerate(females):
                female_vector = self.users_db[female_id]['vector']
                similarity = self._cosine_similarity(male_vector, female_vector)
                similarity_matrix[i, j] = similarity

        # Thuật toán Hungarian tìm MIN, nên ta đảo dấu (hoặc dùng -similarity)
        # để chuyển bài toán MAX thành MIN
        cost_matrix = -similarity_matrix

        # Áp dụng thuật toán Hungarian
        row_indices, col_indices = linear_sum_assignment(cost_matrix)

        # Thu thập kết quả
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

        # Sắp xếp theo điểm giảm dần để dễ đọc
        optimal_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)

        print(f"✅ Đã tìm được {len(optimal_pairs)} cặp ghép tối ưu!")
        print(f"📊 Tổng điểm tương đồng: {total_score:.4f}")
        print(f"📊 Điểm trung bình: {total_score/len(optimal_pairs):.4f}")

        return optimal_pairs, total_score

    def print_optimal_pairs(self, optimal_pairs):
        """
        In ra kết quả ghép cặp tối ưu một cách đẹp mắt
        """
        print("\n" + "="*100)
        print("KẾT QUẢ GHÉP CẶP TỐI ƯU (THUẬT TOÁN HUNGARIAN)")
        print("="*100 + "\n")

        for idx, pair in enumerate(optimal_pairs, 1):
            print(f"Cặp {idx}: User {pair['male_id']} (Nam) ♥ User {pair['female_id']} (Nữ)")
            print(f"  💯 Điểm tương đồng: {pair['similarity_score']:.4f}")
            print(f"  👨 Nam - Năm sinh: {pair['male_info']['year_of_birth']}, Sở thích: {', '.join(pair['male_info']['interests'])}")
            print(f"  👩 Nữ - Năm sinh: {pair['female_info']['year_of_birth']}, Sở thích: {', '.join(pair['female_info']['interests'])}")
            print("-" * 100)

    def save_optimal_pairs_to_file(self, optimal_pairs, total_score, filename="optimal_pairs.txt"):
        """
        Lưu kết quả ghép cặp tối ưu ra file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write("KẾT QUẢ GHÉP CẶP TỐI ƯU (THUẬT TOÁN HUNGARIAN)\n")
            f.write("="*100 + "\n\n")
            f.write(f"Tổng số cặp: {len(optimal_pairs)}\n")
            f.write(f"Tổng điểm tương đồng: {total_score:.4f}\n")
            f.write(f"Điểm trung bình: {total_score/len(optimal_pairs):.4f}\n\n")
            f.write("="*100 + "\n\n")

            for idx, pair in enumerate(optimal_pairs, 1):
                f.write(f"Cặp {idx}: User {pair['male_id']} (Nam) ♥ User {pair['female_id']} (Nữ)\n")
                f.write(f"  💯 Điểm tương đồng: {pair['similarity_score']:.4f}\n")
                f.write(f"  👨 Nam - Năm sinh: {pair['male_info']['year_of_birth']}, Sở thích: {', '.join(pair['male_info']['interests'])}\n")
                f.write(f"  👩 Nữ - Năm sinh: {pair['female_info']['year_of_birth']}, Sở thích: {', '.join(pair['female_info']['interests'])}\n")
                f.write("-" * 100 + "\n\n")

        print(f"✅ Đã lưu kết quả ghép cặp vào file: {filename}")

    def save_optimal_pairs_to_json(self, optimal_pairs, total_score, filename="optimal_pairs.json"):
        """
        Lưu kết quả ghép cặp tối ưu ra file JSON (chỉ thông tin cần thiết)
        """
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

        print(f"✅ Đã lưu kết quả ghép cặp vào file JSON: {filename}")

# --- MAIN DEMO ---
if __name__ == "__main__":
    # 1. Khởi tạo Engine
    engine = DatingEngine()

    # 2. Load dữ liệu từ file JSON (mô phỏng DB)
    engine.load_data_from_json()

    # 3. Lưu vector TRƯỚC khi học
    print("\n--- Lưu Vector TRƯỚC khi tương tác ---")
    engine.save_vectors_to_json("embeddings_before.json")
    engine.save_vectors_to_txt("embeddings_before.txt")

    # 4. Chọn thử 1 user để test (Ví dụ User ID 0)
    TEST_USER_ID = 0
    print(f"\n=== TRƯỚC KHI HỌC (User {TEST_USER_ID}) ===")
    recs_before = engine.get_recommendations(TEST_USER_ID)
    for r in recs_before:
        print(f"User {r['user_id']} ({r['gender']}) - Score: {r['match_score']:.4f} - Sở thích: {r['interests']}")

    # 5. Chạy Training (Cập nhật vector dựa trên rating lịch sử)
    engine.run_training_update()

    # 6. Lưu vector SAU khi học
    print("\n--- Lưu Vector SAU khi tương tác ---")
    engine.save_vectors_to_json("embeddings_after.json")
    engine.save_vectors_to_txt("embeddings_after.txt")

    # 7. Kiểm tra lại kết quả
    print(f"\n=== SAU KHI HỌC (User {TEST_USER_ID}) ===")
    recs_after = engine.get_recommendations(TEST_USER_ID)
    for r in recs_after:
        print(f"User {r['user_id']} ({r['gender']}) - Score: {r['match_score']:.4f} - Sở thích: {r['interests']}")

    print("\nNhận xét: Bạn sẽ thấy danh sách gợi ý thay đổi. Những người có sở thích tương tự những người mà User 0 từng chấm 5 sao sẽ có điểm cao hơn.")
    print(f"\n📁 Đã tạo 4 files: embeddings_before.json, embeddings_before.txt, embeddings_after.json, embeddings_after.txt")

    # 8. Tìm các cặp ghép tối ưu bằng thuật toán Hungarian
    print("\n" + "="*100)
    print("BƯỚC 8: TÌM CẶP GHÉP TỐI ƯU")
    print("="*100)
    optimal_pairs, total_score = engine.find_optimal_pairs()

    # 9. Hiển thị kết quả
    engine.print_optimal_pairs(optimal_pairs)

    # 10. Lưu kết quả ra file
    engine.save_optimal_pairs_to_file(optimal_pairs, total_score, "optimal_pairs.txt")
    engine.save_optimal_pairs_to_json(optimal_pairs, total_score, "optimal_pairs.json")

    print("\n🎉 HOÀN THÀNH! Thuật toán Hungarian đã tìm ra các cặp ghép tối ưu với tổng điểm cao nhất!")