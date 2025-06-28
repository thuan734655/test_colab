# 🚀 Hướng dẫn chạy dự án trên Google Colab

Dự án đã được refactor để có thể chạy trực tiếp trên môi trường Google Colab, tận dụng GPU miễn phí. Do thay đổi chính sách từ ngrok, bạn **bắt buộc** phải có tài khoản và Authtoken để sử dụng.

## Các bước thực hiện

### Bước 1: Lấy Ngrok Authtoken

1.  Đăng ký một tài khoản miễn phí tại [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup).
2.  Sau khi đăng nhập, truy cập trang "Your Authtoken": [https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken).
3.  Sao chép (copy) Authtoken của bạn. Nó sẽ là một chuỗi ký tự dài.

### Bước 2: Thêm Authtoken vào Colab Secrets

Đây là cách an toàn để sử dụng các thông tin nhạy cảm như token.

1.  Trong Notebook Colab của bạn, nhấn vào biểu tượng **chìa khóa (🔑)** ở thanh công cụ bên trái.
2.  Nhấn vào nút **"Add a new secret"**.
3.  Trong ô **Name**, nhập chính xác `NGROK_AUTHTOKEN`.
4.  Trong ô **Value**, dán Authtoken bạn đã sao chép ở Bước 1.
5.  Bật công tắc **"Notebook access"** (cho phép notebook này truy cập secret).

### Bước 3: Mở Google Colab và Cấu hình GPU

1.  Nếu bạn chưa làm, hãy tạo một Notebook mới tại [https://colab.research.google.com/](https://colab.research.google.com/).
2.  Vào menu **Runtime** (Thời gian chạy) -> **Change runtime type** (Thay đổi loại thời gian chạy).
3.  Trong phần **Hardware accelerator** (Trình tăng tốc phần cứng), chọn **GPU** (ví dụ: T4) và nhấn **Save** (Lưu).

### Bước 4: Clone dự án

Dán và chạy đoạn mã sau trong một cell. Đoạn mã này sẽ tự động clone dự án nếu chưa có, hoặc cập nhật nếu đã có sẵn.

```python
# Quan trọng: Hãy đảm bảo bạn sao chép và chạy TOÀN BỘ khối mã bên dưới.
import os

# Bạn có thể thay đổi tên thư mục ở đây nếu muốn, ví dụ: "test_colab"
repo_dir = "test_colab"

repo_url = "https://github.com/thuan734655/test_colab.git"

%cd /content

if not os.path.exists(repo_dir):
    print(f"Cloning repository into './{repo_dir}'...")
    !git clone {repo_url} {repo_dir}
    %cd {repo_dir}
else:
    print(f"Directory '{repo_dir}' already exists. Changing directory and pulling latest changes...")
    %cd {repo_dir}
    !git pull

%env REPO_DIR={repo_dir}
print(f"Project directory set to: /content/{repo_dir}")
```

### Bước 5: Cài đặt môi trường và Dependencies

Chạy cell sau để cài đặt FFmpeg và các thư viện Python cần thiết.

```python
# Cài đặt FFmpeg
!apt-get update && apt-get install -y ffmpeg

# Cài đặt các thư viện Python
!pip install -r requirements.txt
```

### Bước 6: Khởi chạy ứng dụng

Cuối cùng, chạy cell sau để khởi động máy chủ web. Đoạn mã này sẽ tự động lấy Authtoken từ Secrets và khởi chạy ứng dụng.

```python
import os
from google.colab import userdata

# Lấy lại tên thư mục từ biến môi trường đã lưu
repo_dir = os.getenv('REPO_DIR')

# Cố gắng lấy NGROK_AUTHTOKEN từ Colab Secrets
try:
    ngrok_token = userdata.get('NGROK_AUTHTOKEN')
except userdata.SecretNotFoundError:
    print("Lỗi: Secret 'NGROK_AUTHTOKEN' không được tìm thấy. Vui lòng làm theo hướng dẫn ở Bước 2.")
    ngrok_token = None

if ngrok_token and repo_dir and os.path.exists(os.path.join('/content', repo_dir)):
    app_path = os.path.join('/content', repo_dir, 'main_app.py')
    print(f"Launching app from: {app_path}")

    # Chạy ứng dụng với các biến môi trường cần thiết
    !NGROK_AUTHTOKEN={ngrok_token} RUNNING_IN_COLAB=true python {app_path}
else:
    if not repo_dir:
        print("Lỗi: Không tìm thấy thư mục dự án. Vui lòng chạy lại cell ở 'Bước 4' trước.")
    elif not ngrok_token:
        print("Ứng dụng không thể khởi chạy vì thiếu NGROK_AUTHTOKEN.")
```

### Bước 7: Truy cập ứng dụng

1.  Sau khi cell ở Bước 6 chạy thành công, bạn sẽ thấy một dòng output có dạng:
    `INFO:__main__:🔥 Public URL for Colab: http://<some_hash>.ngrok.io`
2.  **Nhấn vào đường link `ngrok` đó** để mở giao diện của ứng dụng trong một tab mới.

**Lưu ý quan trọng:**
*   Không đóng tab Colab và không tắt cell đang chạy ở Bước 6, nếu không ứng dụng sẽ dừng lại.
*   Phiên Colab có giới hạn thời gian. Nếu bị ngắt kết nối, bạn cần chạy lại các cell từ đầu.
