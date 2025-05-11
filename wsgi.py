from app import app

if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc")  # Временный SSL для тестирования


# Gunicorn and WSGI (Web Server Gateway Interface) are both components used in deploying and serving Python web applications, particularly those built with web frameworks like Flask and Django.