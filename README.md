# Chess on Neovim

Finally, this a working demo-ish prototype
Currently Only playable with lichess stockfish
Multiplayer might come soon

## Runtime Dependencies include:
1. berserk
2. chess
3. python-dotenv
4. pynvim
5. python version 3.9 (haven't tested on other versions yet)
6. neovim version 9 (again haven't tested yet since this is a prototype)

for the pip related deps:
`pip3 install berserk chess python-dotenv pynvim`

## Instructions:

### To run
install dependencies and clone the repo to your desired folder

then run a neovim instance from the terminal with the options --listen 127.0.0.1:6789
`nvim --listen 127.0.0.1:6789`

after that run the `threadingmain.py` python file from the repo directory

that should be it


the small windows on top of the board and stats when playing a game is the input window

it acts as console which takes inputs on <CR> / Enter
currently theses commands are defined
'menu' -> return to main menu
'kill_main' -> stop the python executables
'resign' -> for when you accidentally start the match on stockfish level 8
'abort' -> same reason
it treats all other inputs as making a move.
if an illegal move / incorrect move is made it prints to console. does not 
do anything on gui (for now)

Issues:

Highlights make the board updates flicker when making moves [SOLVED]

