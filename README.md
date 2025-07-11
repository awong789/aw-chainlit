This is copy from https://github.com/robrita/tech-blogs





git clone -b Deploy-AI-Agent-App-Service https://github.com/robrita/tech-blogs

copy sample.env to .env and update

python -m venv venv

.\\venv\\Scripts\\activate

python -m pip install -r requirements.txt

chainlit run app.py

