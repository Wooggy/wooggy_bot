# Wooggy Bot
![image info](logo.png)

This telegram bot shows hotel room offers from all over the world.

## Get Started

#### Clone the repository.
`git clone https://github.com/Wooggy/wooggy_bot.git`

#### Create a new bot in telegram.
https://core.telegram.org/bots#creating-a-new-bot/

#### Paste the resulting telegram bot token into the .env
`API_TOKEN=110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`

#### Sign up with Rapidapi
https://rapidapi.com/

#### Get hotels api key and paste into the .env
https://rapidapi.com/apidojo/api/hotels4/

`x-rapidapi-key=7ebe6b2ed7qpl56et23327a70751p15697gwppm3c210591ad2`

#### Use a tunnel (for example NGROK) and insert it into the app.py
https://ngrok.com/

`url = f"https://q9ehy7fvf12a.ngrok.io/{secret}"`

#### Connect to telegram
`https://api.telegram.org/bot<YOUR BOT TOKEN>/setWebhook?url=<YOUR TUNNEL URL>`

#### Start the bot
`flask run`


### Enjoy