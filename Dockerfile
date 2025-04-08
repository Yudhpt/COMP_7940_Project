# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TELEGRAM_ACCESS_TOKEN="7147701749:AAFnVPWxlK4061TaSdl0JLmTaK21CkFlONM" \
    CHATGPT_BASIC_URL="https://genai.hkbu.edu.hk/general/rest" \
    CHATGPT_MODEL_NAME="gpt-4-o-mini" \
    CHATGPT_APIVERSION="2024-05-01-preview" \
    CHATGPT_ACCESS_TOKEN="cac19509-8f9b-428c-8224-fe8a0a33ebc7" \
    FIREBASE_PROJECT_ID="comp7940-c007a" \
    FIREBASE_PRIVATE_KEY_ID="3bf5f0132b972ae6e19e1505042280cbd51cf14a" \
    FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCWh5nqGOUWn49F\n3noHBW+Ok4UlQCWOBSHh5FsMn+LGlG+E6G+Y3caROtqrSMAC1dJgvBqEk9ygx2K3\ni2HLAbw0xAzsZkk3AE9LvVQtiMggPlia7ThRVPRZIvmuZJYe0F9tXmfCDLy60hfK\n1ng+x07/OM3zX23dkG2aSrgkE3aHj1b5ghWCEbDRQG0E1CIA1gC7hUC/Ttk/9wY7\no/kC7JLn/nin+7V6s6AuYB1cfsbqhHUBI7DAa+aoiKEZWMeRylXnhaTpj+tcH48v\nrmsh/Nx5ovNJXHvEOQK7rlHxL8qqcfy7NetGKudX3sJ3Icd3sfyyKxbUVBsw3ml9\n7FNW4h6BAgMBAAECgf9oZT1bw9muU7oiexmggVQUfJNhDekXeYsQicg0b4yHbIkG\nZgAhNxZhkJvrTsPLjb+hO65nM9q3/YyDhls+hSHT2kC4Zu9plYXDJZJMnJw+qECJ\nDle1qTsiqdwtb5no8gFwDKk/5X1e9O6+xr6i6E0T2q+iEoC61CMLvyhut56COM66\nmCpQ7T7DCaLdu0aH6kwwFRJKmiPEWjl+gtD6CH3oqc2o1ALBlwDuF15kW8hux3cp\n/StnbfwfUoIxeSrm1gTfBCt3JvCJtJNGvX59Ci79fr6F6VnF3NuHE69m2xb9P8yM\nkT0ufXoTsrlgEL1Gz5pzpO9n669aNy9ulGB0LCsCgYEA0iSsFh9eB9zpD51dA7Sp\nQYUBooJSbI7JSQTo4ZIR0LAVq5JdYcG9gxsgWErYd73M1PN7+CRvnDzjgF9p5rnn\naWzAL3jcewG1HMbw7pDe83g9mGc9pVickAkW1XWcYZn47inTwIVQNGjuKzfg+Q7j\n6mtIIXhsCBZ4KGKGDnnDF68CgYEAt2C1saSkcyj5rgatW2UIf3UsiRmmTzQ+aid0\njHXyJX0xAdCk37bREgBDaAACme/1lBnw0ntkCm0PqqQFwTqxISChDZUCef24rTMY\nA2BaE6OBeoGXt5fvJp3YySIqHmnW7T3fp47moso0bLEEfU5exjCFLROAsscqs41g\nUJGDiM8CgYBxL4Vs6Po5m/gADA9EZrNfcedeg3kntYSfCsDwdj+YOq+BWPVpKPQN\nQLgcNjv/ysAf1wFntyBSc81JoJqmxmzpMMUXDK8cpd/KHzE4HdmoI5RxmPHwNBkn\nz214Db/sJgWZKfg+0s9PW1ElABTxsN57rcsNFBKEDK4telugQl8dSwKBgH26mxjv\nb6ldoMMG5PlS7l6lciGWKocHpPuXjbt4asv1aBJ8gW65o+MZtx2pVB9DfTdMCefm\nnhLf7+vpheCUYzn5azMqxYXqxiJKc95sw5XPd0kNbX59d4UcmLRe7k3n92q2D5CM\n0+kthoA3ZoKbpzNvtP/Q7V6mW8q71huniW3VAoGALpk8+04r18pzPXDAU0juECAJ\nk4l8FT2E9UNNtQS4suOeHr3wgTHinZJGuZ094fY3jIGq5tN3/wSmRgCoFAc1LzMW\nw+uSpVzX9o3Z1glU+Qi7YI/RnuBAQNoMODGseCpimfzSSo78I0RBnIE6CF60P+xS\na4c2NctANBBUY6EywHU=\n-----END PRIVATE KEY-----\n" \
    FIREBASE_CLIENT_EMAIL="firebase-adminsdk-fbsvc@comp7940-c007a.iam.gserviceaccount.com" \
    FIREBASE_CLIENT_ID="101926560244170176096" \
    FIREBASE_CLIENT_CERT_URL="https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40comp7940-c007a.iam.gserviceaccount.com" \
    LOG_LEVEL="DEBUG" \
    LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s" \
    LOG_FILE="logs/app.log"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY config.ini .
COPY requirements.txt .
COPY codebase/chatbot_GPT.py .
COPY codebase/ChatGPT_HKBU.py .
COPY codebase/recommend.py .
COPY codebase/utils.py .

# 创建日志目录
RUN mkdir -p logs

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（如果需要）
EXPOSE 8080

# 设置启动命令
CMD ["python", "chatbot_GPT.py"]