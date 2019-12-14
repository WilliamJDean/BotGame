import numpy as np
import collections
import gzip

WORDS_UNIVERSE = open('words_10.txt','r').read().split(',')
COUNTERS = {word:collections.Counter(word) for word in WORDS_UNIVERSE}

def score(guess, word):
    """Number of characters in common between two words. For example,
       little and tweety have 2 't' and 1 'e' in common => score is 3."""
    wordCounts  = COUNTERS[word]
    guessCounts = COUNTERS[guess]
    return sum(min(wordCounts[k], guessCounts[k]) for k in wordCounts.keys())

class GameMakerRandomUniform(object):
    def __init__(self, words):
        self.name = 'GameMaker-random-uniform'
        self.words = words

    def pickWord(self):
        return np.random.choice(self.words)
   
class Gamer(object):
    def __init__(self, starter_words):
        """
        The list of remaining candidates is most effectively reduced by guessing the word which partitions the list most evenly.
        For each remaining word in the list, count the number of other words which return a particular score then find the standard
        deviation of the group sizes of each score, found by counting along the rows of a matrix containing all scores of each word 
        against each other. The word with the lowest standard deviation is that which partitions the list most effectively and hence 
        should be guessed.

        Once a word has been guessed and we have not won the game, we can remove that word from the list given the definition of
        having not won. This ensures that the guesses can not get stuck in a loop of guessing the same word and definitely losing.
       
        This process is then applied iteratively.
        """
        print('Initialising Gamer!')
        self.name = 'Best partition Gamer'
        self.idx = 0
        self.words = np.array([])
        self.starter_words = np.array(starter_words)
       
        self.starter_AllScores = np.load('AllScores.pny')
        self.AllScores = np.array([])
        self.deviations = np.array([])
        print('Gamer ready!')

    def prepareForNewGame(self):
        """
        After each game, the words and scores matrix must be reset to copies of the original set to begin the game fresh. The index must be reset to zero.
        """
        self.words = self.starter_words.copy()
        self.AllScores = self.starter_AllScores.copy()
        self.idx = 0

    def resultOfGuess(self, wordGuessed, scoreOfThatGuess):
        self.idx += 1
        """
        For a guessed word, we can lookup its position in the words array. Then, generate a Boolean mask for which scores match the
        returned score from the guess. We can then apply this Boolean to cut down the list of possible words to only those with the
        correct score. The same mask can then be used to cut down the rows then columns of the AllScores matrix. Once the AllScores
        has been cut down, it is trivial to find the new deviations.
        
        We can also remove whichever word we guessed, as by the game not ending it was not the correct word.
        """
        x = np.where(self.words == wordGuessed)[0][0]
        Guess_Scores = self.AllScores[x]
        BoolMask = (Guess_Scores == scoreOfThatGuess)
        BoolMask[x] = 0 #   This corresponds to the wordGuessed, which we can remove
        #   Now reduce the list of words to that which is allowed
        self.words = self.words[BoolMask]
        #   Reduce the AllScores matrix to contain only rows that remain
        self.AllScores = self.AllScores[BoolMask]
        #   Now allow only the columns to remain
        self.AllScores = self.AllScores[:, BoolMask]
        #   Ensure AllScores is square matrix, or error
        assert (len(self.AllScores) == len(self.AllScores[0])), "Error in AllScores, not square matrix"
        #   Now update the standard deviations, reset as append method called
        self.deviations = np.zeros(len(self.AllScores))
        for row in range(len(self.AllScores)):
            unique, counts = np.unique(self.AllScores[row], return_counts=True)
            self.deviations[row] = np.std(counts)
        
    def guessWord(self):
        """      
        For the first guess we know the group sizes a priori, so know the word which minimises the standard deviation and so the
        word first guessed is fixed as 'alliancing'.
       
        After that, we guess the word with the lowest deviation as this best partitions the remaining words.
        """
        if self.idx == 0:
            return 'alliancing'     
        else:
            return self.words[np.where(self.deviations == min(self.deviations))][0]

def measureResults(gameWords, numberOfGames = 100):
    """
    3 changes were made to port to Python 3.x:
    in measureResults() xrange -> range,
    in score() wordCounts.iterkeys() -> wordCounts.keys()
    Brackets added all over to print statements
    """
    # Run the game a certain number of times then return the results
    gameMaker = GameMakerRandomUniform(list(gameWords))
    gamer = Gamer(list(gameWords))
    result = 0
    for i in range(numberOfGames):
        # run sequentially different games
        # tell strategy that previous game ended
        gamer.prepareForNewGame()
        # GameMaker picks a word that Gamer will try to guess
        word = gameMaker.pickWord()
        assert word in gameWords
        payout = len(word)
        #print("New Game : %s"%word)
        while payout:
            # let gamer guess a word
            guess = gamer.guessWord()
            #print("Guess is %s for payout of %s"%(guess,payout))
            if guess == word: # Gamer wins
                break
            else:
                payout -= 1 # reduce the payout
                gamer.resultOfGuess(guess, score(guess,word))
        # This game ended, do the accounting before moving to next game
        result += payout
    # report results
    print ('"%s"'%gamer.name ,'scored %s against'%(result / float(numberOfGames)),'"%s"'%gameMaker.name)
    print ("\tFinal result",result / float(numberOfGames))
    return result / float(numberOfGames)

if __name__ == '__main__':
        measureResults(WORDS_UNIVERSE)

