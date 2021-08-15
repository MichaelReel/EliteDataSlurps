# Elite Data Slurps

  - Just want to create an simple script that will record locally:
    - the locations of the highest sell prices
    - the locations of the lowest buy prices 
  - for each commodity
  - by parsing the EDDN data packets
  - show the best trades across the "bubble"

### Really basic (and probably wrong/incomplete) instructions:

Install python3 and make sure it's on your PATH if you don't have it already.

get requirements:
`pip install -r requirements.txt`

run slurper:
`python3 slurper.py`

### Basic tips for running the current code:

  - The output is currently a table irregularly printed to the command line every few seconds depending on the rate of messages from EDDN.
  - Recommended to run the slurper in a separate terminal window that can accomodate over 100 characters wide and 60 lines high.
  - Not recommended to use a large text buffer or a large/infinite scroll-back limit.
  - Sigint (`Ctrl` + `C`) should stop the slurper and save any docks/stocks recorded.
  - Each column of the output is:
    - `{Buy or Sell}`
    - `@` 
    - `{Price}`
    - `{< or >}`
    - `{System Name}`
    - `{Station Name}`
    - `{M/A/ }` - M - medium parking only. A - Asteroid base. Blank means the station should accomodate large vessels.
    - `{Distance to best trade}` - For "Buy" rows this is distance to the best "Sell". For "Sell" rows this is the distance to the best "Buy".
    - `{Distance to station}` - How far to travel within the local system to get to the station.
    - `{Data age}` - How old the data is in days, and Hours:Minutes:Seconds
  - The output only includes the top 5 commodities and the top 5 buys and top 5 sells in each.
  - The top best buys are in ascending (to best) order and the top best sales are in descending (from best) order - this means the best trades are in the MIDDLE rows of each section.
  - Recommended to run the [EDMarketConnector](https://github.com/EDCD/EDMarketConnector/wiki) when playing Elite so that you can keep your own slurper data up to date.