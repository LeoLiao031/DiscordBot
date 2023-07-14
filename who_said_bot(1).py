# import the co:here api for machine learning
import cohere
import csv
import discord
from discord.ext import commands
from multiprocessing import Process
from multiprocessing import Pool
api_key =
co = cohere.Client(api_key)
from cohere.classify import Example
people = 'people1-3000.csv'
people2 = 'people3001-6001.csv'
people3 = 'people6002-7087.csv'
bot_file = 'who_said_bot.py'
file_list = [people, people2, people3, bot_file]
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

def read_csv(csv_name):
    with open(csv_name, encoding="utf8") as f:
        csv_reader = csv.reader(f)
        statement = []
        result = []
        for line in csv_reader:
            statement.append(line[0])
            result.append(line[1])
        return (statement, result)

# classification will help us identify who wrote a message
def classification(str_to_analyse: str, csv_files: list[str]):
    examples = generate_examples(csv_files, 0, 1)
    inputs = [str_to_analyse]
    response = co.classify(
      model='small',
      inputs=inputs,
      examples=examples)

    return(response.classifications)


# function that will parse cohere object into tuple of (name, confid)
def parse_data(cohere_obj) -> tuple[str, float]:
    # find the prediction first
    str_cohere_object = str(cohere_obj).replace('\"', '').replace('<', '').replace('>', '').replace(']', '')
    index_predic = str_cohere_object.find('prediction: ') + len('prediction: ')
    data_list = str_cohere_object[index_predic:].replace(' confidence: ', '').split(',')
    # print('data_list: ', data_list)
    data_list[1] = round(float(data_list[1]), 2)
    return tuple(data_list)


## this function reads the co:here object and returns a tuple of the result
#def predic_confid_json(returnstr):
    #def parse_data(str_to_parse: str, keyword: str):
        #LEEWAY = 15
        #keyword_indice = str_to_parse.find(keyword) + len(keyword)
        #str_to_parse = str_to_parse[keyword_indice:keyword_indice + LEEWAY]
        #str_to_parse = str_to_parse[str_to_parse.find('\n')-1::-1]
        ## reversing the resultant as we read the string backwards
        #resultant = str_to_parse[::-1]
        #return resultant


    ##isolating the prediction

    #prediction = parse_data(returnstr, 'prediction: ')
    ##searching for the prediction and its matching confidence level
    #str_to_find = (prediction+'\n\tconfidence: 0')
    #confidence = parse_data(returnstr, str_to_find)

    #return (prediction, confidence)

# turning the CSV file into training data for the machine learning algorithm
def generate_examples(csv_files: list[str], statement_indice: int, result_indice: int):
    example_list = []
    for csv_file in csv_files:
        training_data = read_csv(csv_file)
        for i in range(len(training_data[statement_indice])):
            example_list.append(Example(training_data[statement_indice][i],
                                        training_data[result_indice][i]))
    return example_list


# function that will take a message and break it down into a list of
# sentences that analyse one by one
def breakdown_text(text: str) -> list[str]:
    # delimiter to split paragraph is the period
    sentences = text.split('.')
    return sentences


def out_of_three(guesses: list):
    print('p1: ', guesses[0])
    print('p2: ', guesses[1])
    print('p3: ', guesses[2])
    name_confid = {}
    list_guesses = []
    for tuples in guesses:
        list_guesses.extend(list(tuples))
    for people in guesses:
        if people[0] not in name_confid:
            name_confid[people[0]] = float(people[1])
        else:
            name_confid[people[0]]+=float(people[1])
    max_value = max(name_confid, key=name_confid.get)
    # dont want decimal greater than 1
    return (max_value, name_confid[max_value]/list_guesses.count(max_value))


def pool_handler(text, pool):
    work = ([text, people], [text, people2], [text, people3])
    values = pool.map(who_said, work)
    return values


bot = commands.Bot(intents=discord.Intents.all(), command_prefix='.')

@bot.command()
async def hello(ctx):
    await ctx.reply('Hello!')


def process_results(results: list[tuple[str, float]]) -> tuple[str, float]:
    # find the speaker with the highest confidence level
    most_likely_speaker = max(results, key=lambda x: x[1])
    return most_likely_speaker


def faster_said(sentences: list[str], csv_files: list[str]) -> list[tuple[str, float]]:
    # define a regular function to classify each sentence
    def classify_sentence(sentence):
        return classification(sentence, csv_files)

    # create a pool of processes
    with Pool() as pool:
        # classify each sentence in parallel
        results = pool.map(classify_sentence, sentences)

    # flatten the list of results
    results = [item for sublist in results for item in sublist]

    return results



# update the who_said command to split the text into sentences and pass the list of sentences to the faster_said method
@bot.command()
async def said(ctx, *, text: str):
    start_time = time.perf_counter()

    # create a list of CSV files
    csv_files = ['people1-3000.csv', 'people3001-6001.csv', 'people6002-7087.csv']

    sentences = breakdown_text(text)
    results = faster_said(sentences, csv_files)

    # process the results and return the most likely speaker
    speaker, confidence = process_results(results)
    await ctx.send(f"I'm {confidence*100:.0f}% sure that {speaker} said: {text}")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    await ctx.send(f"The who_said command took {elapsed_time:.4f} seconds to execute.")





@bot.command()
async def files(ctx):
    for file in file_list:
        await ctx.send(file=discord.File(file))


@bot.command()
async def cohere_classification(ctx, sentence):
    await ctx.send(classification(sentence, people))


bot.run('')
