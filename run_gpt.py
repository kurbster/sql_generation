#!/usr/bin/env python3
import json
import openai

prompt ="""
You are given a schema for a SQL dataset. You should generate a question related to the dataset and the appropriate SQL query.

Tables:

    book_club:
    book_club_id|Year|Author_or_Editor|Book_Title|Publisher|Category|Result
    1|1989|Michael Nava|Goldenboy|Alyson|Gay M/SF|Won [A ]
    2|1989|Donald Ward|Death Takes the Stage|St. Martin's Press|Gay M/SF|Nom
    3|1989|Michael Bishop|Unicorn Mountain|William Morrow|Gay M/SF|Nom
    4|1989|Joseph Hansen|Obedience|Mysterious Press|Gay M/SF|Nom
    5|1989|George Baxt|Whoӳ Next|International Polygonics|Gay M/SF|Nom
    6|1989|Antoinette Azolakov|Skiptrace|Banned Books|Lesb. M/SF|Won
    7|1989|Claire McNab|Lessons In Murder|Naiad Press|Lesb. M/SF|Nom
    8|1989|Judy Grahn|Mundaneӳ World|Crossing Press|Lesb. M/SF|Nom
    9|1989|Dolores Klaich|Heavy Gilt|Naiad Press|Lesb. M/SF|Nom
    10|1989|Sandy Bayer|The Crystal Curtain|Alyson|Lesb. M/SF|Nom
    11|1990|Jeffrey N. McMahan|Somewhere in the Night|Alyson|Gay SF/F|Won [B ]
    12|1990|Thom Nickels|Walking Water / After All This|Banned Books|Gay SF/F|Nom

    movie:
    movie_id|Title|Year|Director|Budget_million|Gross_worldwide
    1|The Boondock Saints|1999|Troy Duffy|6.0|30471
    2|The Big Kahuna|1999|John Swanbeck|7.0|3728888
    3|Storm Catcher|1999|Anthony Hickox|5.0|40500
    4|Jill Rips|2000|Anthony Hickox|4.0|456774
    5|The Whole Nine Yards|2000|Jonathan Lynn|41.3|106371651
    6|Battlefield Earth|2000|Roger Christian|44.0|29725663
    7|Get Carter|2000|Stephen Kay|63.6|19412993
    8|The Art of War|2000|Christian Duguay|60.0|40400425
    9|Agent Red|2000|Damian Lee|47.0|543356
    10|3000 Miles to Graceland|2001|Demian Lichtenstein|62.0|18720175

    culture_company:
    Company_name|Type|Incorporated_in|Group_Equity_Shareholding|book_club_id|movie_id
    Culture China|Corporate|China|18.77|1|2
    Culture China Cargo|Joint Venture|China|49.0|2|3
    Culture Hong Kong|Joint Venture|Hong Kong|60.0|3|4
    Dragonair|Subsidiary|Hong Kong|100.0|5|7
    Cathay Pacific Culture|Subsidiary|Hong Kong|100.0|5|5
    Cathay Pacific Culture Services (HK) Limited|Subsidiary|Hong Kong|100.0|6|

    Question: What are all the company names that have a book published by Alyson?
    SQL: SELECT T1.company_name FROM culture_company AS T1 JOIN book_club AS T2 ON T1.book_club_id  =  T2.book_club_id WHERE T2.publisher  =  'Alyson'

    Question: What are the titles of movies and books corresponding to companies incorporated in China?
    SQL: SELECT T1.title ,  T3.book_title FROM movie AS T1 JOIN culture_company AS T2 ON T1.movie_id  =  T2.movie_id JOIN book_club AS T3 ON T3.book_club_id  =  T2.book_club_id WHERE T2.incorporated_in  =  'China'

    Question: What is the publisher with most number of books?
    SQL: SELECT publisher FROM book_club GROUP BY publisher ORDER BY count(*) DESC LIMIT 1

    Question: How many books fall into each category?
    SQL: SELECT category ,  count(*) FROM book_club GROUP BY category

    Question: List categories that have at least two books after year 1989?
    SQL: SELECT category FROM book_club WHERE YEAR  >  1989 GROUP BY category HAVING count(*)  >=  2

    Tables:

    architect:
    id|name|nationality|gender
    1|Frank Lloyd Wright|American|male
    2|Frank Gehry|Canadian|male
    3|Zaha Hadid|Iraqi, British|female
    4|Mies Van Der Rohe|German, American|male
    5|Le Corbusier|Swiss, French|male

    bridge:
    architect_id|id|name|location|length_meters|length_feet
    1|1|Xian Ren Qiao (Fairy Bridge)|Guangxi , China|121.0|400.0
    2|2|Landscape Arch|Arches National Park , Utah , USA|88.0|290.0
    3|3|Kolob Arch|Zion National Park , Utah , USA|87.0|287.0
    4|4|Aloba Arch|Ennedi Plateau , Chad|76.0|250.0
    5|5|Morning Glory Natural Bridge|Negro Bill Canyon , Utah , USA|74.0|243.0
    5|6|Rainbow Bridge|Glen Canyon National Recreation Area , Utah , USA|71.0|234.0
    4|7|Gaotun Natural Bridge|Guizhou , China|70.0|230.0
    3|8|Sipapu Natural Bridge|Natural Bridges National Monument , Utah , USA|69.0|225.0
    2|9|Stevens Arch|Escalante Canyon , Utah , USA|67.0|220.0
    1|10|Shipton's Arch|Xinjiang , China|65.0|212.0
    1|11|Jiangzhou Arch|Guangxi , China|65.0|212.0
    1|12|Hazarchishma Natural Bridge|Bamiyan Province , Afghanistan|64.2|210.6
    2|13|Outlaw Arch|Dinosaur National Monument , Colorado , USA|63.0|206.0
    2|14|Snake Bridge|Sanostee , New Mexico , USA|62.0|204.0
    5|15|Wrather Arch|Wrather Canyon , Arizona , USA|75.0|246.0

    mill:
    architect_id|id|location|name|type|built_year|notes
    1|1|Coswarem|Le Vieux Molen|Grondzeiler|1840|Molenechos (Dutch)
    1|2|Donceel|Moulin Bertrand|Grondzeiler|1890|Molenechos (Dutch)
    2|3|Fexhe-le-haut-Clocher|Moulin de Fexhe|Grondzeiler|1843|Molenechos (Dutch)
    3|4|Momalle|Moulin de Momalle|Bergmolen|1850|Molenechos (Dutch)
    4|5|Othée|Moulin du Château|Grondzeiler|1856|Molenechos (Dutch)
    4|6|Pousset|Moulin de Pousset|Grondzeiler|1819|Molenechos (Dutch)

    Generate multiple diverse question and SQL pairs. The queries should involve multiple tables and include a GROUP BY statement.

    Question:
"""

api_cfg = {
        "engine": "text-davinci-002",
        "top_p": 1.0,
        "temperature": 0.7,
        "max_tokens": 1024,
        "presence_penalty": 2.0,
        "frequency_penalty": 2.0,
        #"echo": True,
}

num_completions = 1

def main():
    global prompt
    output = "Question:\n\n"
    for i in range(num_completions):
        prompt += output
        response = openai.Completion.create(
            prompt=prompt,
            **api_cfg
        )

        with open(f'./ravioli_response_{i}.json', 'w') as f:
            json.dump(response, f, indent=4)

        output = response['choices'][0]['text'] + "Question:\n\n"

if __name__ == '__main__':
    main()
