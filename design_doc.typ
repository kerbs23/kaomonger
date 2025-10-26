= Overview
This is the design doc for a python script to scrape emojicombos.com and process it into nice terminal-safe json.
This takes the form of a terminal script that scrapes the website for a desired search term (just in the url), and then pull out the content and all of the user generated tags into a temporary "messy json" in the wd.
Then, for each kaomoji in the messy json, one at a time, we run a whole bunch of regexes on it to auto-populate some sections, and open the json in a vim directory so that I can edit the tags and so forth.
Then, the cleaned up kaomoji will get put into a big ol db file.

= Json Format
```json
{
    "emoji_id": {
        "content": "The contents of the emoji",
        "species": ["species of the kaomoji", "more species"],
        "emotion": ["the emotions in the kaomoji", "more emotions"],
        "misc"     : ["misc tags", "more misc tags"],
        "dotArt": false,
        "hasEmoji": false,
        "multiLine": false
    }
}
```
emoji_id is a identifying number assigned for each emoji. just hash the messy json for that kaomoji
content is the text of the emoji itself. When this gets put into the vim buffer it needs to be outside of the json curly braces so it looks good, and maybe we do some regex to turn the nonsense unicode whitespaces into like the empty brail char, so that it gets saved thru paste and such.
The species is a tag like cat or bunny, or something more abstract like monar or :3. The issue with this and the emotion tag is that I want them to be arbitrarily assigned but pulled from a relatively small set. Ideal would be all previous entries get added to my autocomplete list in vim-- I think the best play is to just maintain a list of each and temporarily shwack it to the bottom of the thing when I open it im nvim so it matches on just typed text. This also lets us regex the user tags and try to match them for species/emotions and try to auto populate some things.
Emotion is similar to species but for the words that make up the tags.
misc is just arbitrary tags, no restrictions or tracking or whatever.
dotArt regexes for if its all chars like "⠛⠻⠿" and if it is just that or whitespace then it is true. This is in the json so I can manually change it
hasEmoji is dotArt but for unicode emojis like "🐰"
multiLine is hasEmoji but for <Cr> or any other like newline thing



list of the dots for dotArt: {"⠀":"⣿","⠁":"⣾","⠂":"⣽","⠃":"⣼","⠄":"⣻","⠅":"⣺","⠆":"⣹","⠇":"⣸","⠈":"⣷","⠉":"⣶","⠊":"⣵","⠋":"⣴","⠌":"⣳","⠍":"⣲","⠎":"⣱","⠏":"⣰","⠐":"⣯","⠑":"⣮","⠒":"⣭","⠓":"⣬","⠔":"⣫","⠕":"⣪","⠖":"⣩","⠗":"⣨","⠘":"⣧","⠙":"⣦","⠚":"⣥","⠛":"⣤","⠜":"⣣","⠝":"⣢","⠞":"⣡","⠟":"⣠","⠠":"⣟","⠡":"⣞","⠢":"⣝","⠣":"⣜","⠤":"⣛","⠥":"⣚","⠦":"⣙","⠧":"⣘","⠨":"⣗","⠩":"⣖","⠪":"⣕","⠫":"⣔","⠬":"⣓","⠭":"⣒","⠮":"⣑","⠯":"⣐","⠰":"⣏","⠱":"⣎","⠲":"⣍","⠳":"⣌","⠴":"⣋","⠵":"⣊","⠶":"⣉","⠷":"⣈","⠸":"⣇","⠹":"⣆","⠺":"⣅","⠻":"⣄","⠼":"⣃","⠽":"⣂","⠾":"⣁","⠿":"⣀","⡀":"⢿","⡁":"⢾","⡂":"⢽","⡃":"⢼","⡄":"⢻","⡅":"⢺","⡆":"⢹","⡇":"⢸","⡈":"⢷","⡉":"⢶","⡊":"⢵","⡋":"⢴","⡌":"⢳","⡍":"⢲","⡎":"⢱","⡏":"⢰","⡐":"⢯","⡑":"⢮","⡒":"⢭","⡓":"⢬","⡔":"⢫","⡕":"⢪","⡖":"⢩","⡗":"⢨","⡘":"⢧","⡙":"⢦","⡚":"⢥","⡛":"⢤","⡜":"⢣","⡝":"⢢","⡞":"⢡","⡟":"⢠","⡠":"⢟","⡡":"⢞","⡢":"⢝","⡣":"⢜","⡤":"⢛","⡥":"⢚","⡦":"⢙","⡧":"⢘","⡨":"⢗","⡩":"⢖","⡪":"⢕","⡫":"⢔","⡬":"⢓","⡭":"⢒","⡮":"⢑","⡯":"⢐","⡰":"⢏","⡱":"⢎","⡲":"⢍","⡳":"⢌","⡴":"⢋","⡵":"⢊","⡶":"⢉","⡷":"⢈","⡸":"⢇","⡹":"⢆","⡺":"⢅","⡻":"⢄","⡼":"⢃","⡽":"⢂","⡾":"⢁","⡿":"⢀","⢀":"⡿","⢁":"⡾","⢂":"⡽","⢃":"⡼","⢄":"⡻","⢅":"⡺","⢆":"⡹","⢇":"⡸","⢈":"⡷","⢉":"⡶","⢊":"⡵","⢋":"⡴","⢌":"⡳","⢍":"⡲","⢎":"⡱","⢏":"⡰","⢐":"⡯","⢑":"⡮","⢒":"⡭","⢓":"⡬","⢔":"⡫","⢕":"⡪","⢖":"⡩","⢗":"⡨","⢘":"⡧","⢙":"⡦","⢚":"⡥","⢛":"⡤","⢜":"⡣","⢝":"⡢","⢞":"⡡","⢟":"⡠","⢠":"⡟","⢡":"⡞","⢢":"⡝","⢣":"⡜","⢤":"⡛","⢥":"⡚","⢦":"⡙","⢧":"⡘","⢨":"⡗","⢩":"⡖","⢪":"⡕","⢫":"⡔","⢬":"⡓","⢭":"⡒","⢮":"⡑","⢯":"⡐","⢰":"⡏","⢱":"⡎","⢲":"⡍","⢳":"⡌","⢴":"⡋","⢵":"⡊","⢶":"⡉","⢷":"⡈","⢸":"⡇","⢹":"⡆","⢺":"⡅","⢻":"⡄","⢼":"⡃","⢽":"⡂","⢾":"⡁","⢿":"⡀","⣀":"⠿","⣁":"⠾","⣂":"⠽","⣃":"⠼","⣄":"⠻","⣅":"⠺","⣆":"⠹","⣇":"⠸","⣈":"⠷","⣉":"⠶","⣊":"⠵","⣋":"⠴","⣌":"⠳","⣍":"⠲","⣎":"⠱","⣏":"⠰","⣐":"⠯","⣑":"⠮","⣒":"⠭","⣓":"⠬","⣔":"⠫","⣕":"⠪","⣖":"⠩","⣗":"⠨","⣘":"⠧","⣙":"⠦","⣚":"⠥","⣛":"⠤","⣜":"⠣","⣝":"⠢","⣞":"⠡","⣟":"⠠","⣠":"⠟","⣡":"⠞","⣢":"⠝","⣣":"⠜","⣤":"⠛","⣥":"⠚","⣦":"⠙","⣧":"⠘","⣨":"⠗","⣩":"⠖","⣪":"⠕","⣫":"⠔","⣬":"⠓","⣭":"⠒","⣮":"⠑","⣯":"⠐","⣰":"⠏","⣱":"⠎","⣲":"⠍","⣳":"⠌","⣴":"⠋","⣵":"⠊","⣶":"⠉","⣷":"⠈","⣸":"⠇","⣹":"⠆","⣺":"⠅","⣻":"⠄","⣼":"⠃","⣽":"⠂","⣾":"⠁","⣿":"⠀"}
