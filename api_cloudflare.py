from selenium import webdriver
import requests

# Đường dẫn đến trang web bạn muốn crawl
url = "https://batdongsan.com.vn"


# Cloudflare API key của bạn
cloudflare_api_key = "900c8f7bde00a5bf4ea05488a47e24ccf1d28"

# Sử dụng Cloudflare API key để gửi yêu cầu API và tắt tính năng bảo vệ
def disable_cloudflare_protection(url, api_key):
    try:
        # Tạo yêu cầu API
        payload = {
            "targets": [
                {
                    "target": url,
                    "value": "default",
                }
            ],
            "value": "off",
        }

        headers = {
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        # Gửi yêu cầu API
        response = requests.patch(
            "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/settings/security_level",
            json=payload,
            headers=headers,
        )

        # Kiểm tra phản hồi
        if response.status_code == 200:
            print("Đã tắt tính năng bảo vệ của Cloudflare thành công!")
        else:
            print("Không thể tắt tính năng bảo vệ của Cloudflare. Mã lỗi:", response.status_code)
    except Exception as e:
        print("Lỗi khi gửi yêu cầu API:", str(e))

# Khởi tạo trình duyệt Chrome thông thường (trình duyệt thực thụ)
driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options = opt)

# Sử dụng API key để tắt tính năng bảo vệ của Cloudflare
disable_cloudflare_protection(url, cloudflare_api_key)

# Mở URL của trang web bạn muốn truy cập
driver.get(url)
driver.find_element(By.CLASS_NAME, 're__icon-search--sm').click()

# Tiếp tục thao tác trên trang web như thông thường
# Ví dụ: lấy tiêu đề của trang
page_title = driver.title

# Đóng trình duyệt
driver.quit()