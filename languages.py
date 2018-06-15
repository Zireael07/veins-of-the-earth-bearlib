# coding: utf8
import random

VOWELS = [ "a", "e", "i", "o", "u"]

CONSONANTS_LABIALS = [ "p", "b", "f"]
CONSONANTS_NASALS = ["m", "n"]
CONSONANTS_DENTALS = ["t", "d"]
CONSONANTS_SIBILANTS = [ "s", "sh"]
CONSONANTS_LIQUIDS = ["l", "r"]
CONSONANTS_VELAR = ["k", "g"]

SYLLABLE_TYPES = [ "CV", "CVV"]

INVENTORY_WEIGHTS = [
    ("SIMPLE", 90),
    ("COMPLEX", 100)
]

INVENTORY_TYPES = {
    "SIMPLE" : [CONSONANTS_LABIALS, CONSONANTS_DENTALS, CONSONANTS_VELAR],
    "COMPLEX" : [CONSONANTS_LABIALS, CONSONANTS_DENTALS, CONSONANTS_VELAR, CONSONANTS_SIBILANTS, CONSONANTS_LIQUIDS]
}

def get_result(roll, table):
    #print(str(table))
    import bisect
    breakpoints = [k[1] for k in table if k[1] < 100]
    breakpoints.sort()

    # print breakpoints

    i = bisect.bisect(breakpoints, roll)
    res = table[i][0]

    return res


class Language(object):
    def __init__(self, seed):
        self.seed = seed
        self.consonants = []

        random.seed(seed)

        self.consonants = self.generate_language()


    def generate_language(self):
        # select available consonants
        options = self.pick_consonant_inventory()
        consonants = []
        for o in INVENTORY_TYPES[options]:
            # print(o)
            for l in o:
                consonants.append(l)

        return consonants

    def pick_consonant_inventory(self):
        #import generators
        #d100 = generators.roll(1, 100)
        d100 = random.randint(1,100)
        #print(str(d100))

        res = get_result(d100, INVENTORY_WEIGHTS)

        #res = generators.get_result(d100, INVENTORY_WEIGHTS)

        print res
        return res


    def generate_syllable(self, kind):
        char_list = list(kind)
        #print char_list
        letters = []
        for i in range(len(char_list)):
            if char_list[i] == "C":
                letters.append(random.choice(self.consonants))
            elif char_list[i] == "V":
                letters.append(random.choice(VOWELS))

        s = ''.join(letters)
        # print s
        return s

    def generate_word(self, num_syllables):
        #random.seed(seed)
        print("Generating word...")


        letters = []
        for i in range(num_syllables):
            syllable = random.choice(SYLLABLE_TYPES)
            str = self.generate_syllable(syllable)
            letters.append(str)

        word = ''.join(letters)
        print word
        return word

    def generate_sentence(self, num_words):
        #random.seed(seed)
        sent = []
        for i in range(num_words):
            w = self.generate_word(3)
            sent.append(w)

        sent = ' '.join(sent)
        print sent
        return sent

    # This can ONLY ever take one parameter, i.e. match!
    def language_replace(self, match):
        '''
        Replace a single word with a new one
        :param match: re.matchobj
        :return: new word
        '''
        word = match.group()

        if word is not None:
            if len(word) > 4:
                new_word = self.generate_word(3)
            else:
                new_word = self.generate_word(2)
        else:
            new_word = None

        return new_word

if __name__ == '__main__':

    lang = Language(20)

    lang.generate_sentence(4)
    lang.generate_word(3)
    lang.generate_word(2)
    lang.generate_word(2)