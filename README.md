# Poker

Left side of the screen displays the playing field log, each command is registered in the log.

Main buttons:<br />
Start - starts the game<br />
Apply - applies the stacks to all players based on the value inputted in the box<br />
Reset - resets the game<br />

You need to apply the stacks before pressing start, otherwise the base value will be applied (10000).

Gameplay buttons:<br />
Fold - player folds immediately<br />
Check - player checks<br />
Call - players calls the amount required to continue the game<br />
Bet 20 - player bets 20 chips<br />
-/+ buttons between bet - change the amount to bet<br />
Raise 40 - player raises 40 chips<br />
-/+ buttons between raise - change the amount to raise<br />
All in - player goes all in

After the game ends the hand that was saved to database is displayed on the right section of a screen.

Refresh history button refreshes and lists all the information contained in the database.

Deployment:<br />
docker-compose up --build<br />
