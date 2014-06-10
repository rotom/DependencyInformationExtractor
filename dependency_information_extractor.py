import sys, os
import enchant

from collections import defaultdict

from parsed_ukwac_reader import *

## create recursive tree
tree = lambda: defaultdict(tree)

## load spell checkers
D_US = enchant.Dict('en_US')
D_GB = enchant.Dict('en_GB')

## define the header

class SentenceInformation(object):

    def __init__(self, sentence, validate=True, verbose=False):
        self.sentence = sentence

        self._extract_information(verbose)
        self._validate_information(validate)

    def _extract_information(self, verbose):
        
        self.information = tree()

        word_gen = self.sentence.get_word(pos='^V', 
                                          return_word=True, 
                                          return_lemma=True, 
                                          return_pos=True, 
                                          return_index=True,
                                          return_relation=True)

        for word, lemma, pos, index, relation in word_gen:

            try:
                verb_info = VerbInformation(sentence=self.sentence, 
                                            word=word, 
                                            lemma=lemma,
                                            pos=pos,
                                            index=index, 
                                            relation=relation,
                                            validate=validate)

                self.information[index] = verb_info
            except (ValueError, AssertionError) as e:
                pass # implement logging here

    def _validate_information(self, validate):
        if not self.information:
            raise ValueError, 'no information was gathered from this sentence'
        elif validate:
            self._validate_matrix_flags()

    def _validate_matrix_flags(self):
        try:
            info_iter = self.information.itervalues()
            matrix_info = [verb_info for verb_info in info_iter if verb_info.matrix == 'true']
        except TypeError:
            raise ValueError, 'there must be one matrix verb'

        if len(matrix_info) > 1:
            raise ValueError, 'only one verb can be the matrix verb'

    def get_matrix_information(self, require_matrix=True):
        for verb_info in self.information.itervalues():
            if verb_info.matrix == 'true':
                return verb_info
        else:
            if require_matrix:
                raise ValueError, 'there is no matrix verb'
            else:
                raise NotImplementedError, 'need to implement mechanism for when no matrix verb exists'

    def get_information_with_highest_index(self, index):
        for verb_info in self.information.itervalues():
            if verb_info.highest_index == index:
                return verb_info
        else:
            raise ValueError, 'embedded index not found'
       
    def get_data(self, datahead):
        return [word.get_data(datahead) for word in self.information.itervalues()]

class WordInformation(object):

    # VB	be    base (be)
    # VBD	be    past tense (went)
    # VBG	be    -ing (being)
    # VBN	be    past participle (been)
    # VBP	be    plural (are)
    # VBZ	be    -s (is)
    # VH	have  base (have)
    # VHD	have  past tense (had)
    # VHG	have  -ing (having)
    # VHN	have  past participle (had)
    # VHP	have  plural (have)
    # VHZ	verb  -s (believes)
    # VV	verb  base (believe)
    # VVD	verb  past tense (believed)
    # VVG	verb  -ing (believing)
    # VVN	verb  past participle (believed)
    # VVP	verb  plural (believe)
    # VBZ	verb  -s (believes)

    # JJ	adjective, general (near)
    # JJR	adjective, comparative (nearer)
    # JJS	adjective, superlative (nearest)

    # RB	adverb, general (chronically, deep)
    # RBR	adverb, comparative (easier, sooner)
    # RBS	adverb, superlative (easiest, soonest)

    # NN	noun, common singular (action)
    # NNS	noun, common plural (actions)
    # NP	noun, proper singular (Thailand, Thatcher)
    # NPS	noun, proper plural (Americas, Atwells)
    # PP	pronoun, personal (I, he)
    # PP$	pronoun, possessive (my, his)

    # WDT	det, wh- (what, which, whatever, whichever)
    # WP	pronoun, wh- (who, that)
    # WP$	pronoun, possessive wh- (whose)
    # WRB	adv, wh- (how, when, where, why)

    # $	currency symbol ($)
    # ''	closing quotes (")
    # (	opening parentheses (()
    # )	closing parentheses ())
    # ,	comma (,)
    # :	connecting punctuation (:, -, ...)
    # ``	opening quotes (")

    # CC	conjunction, coordinating (and)
    # CD	number, cardinal (four)
    # DT	determiner, general (a, the, this, that)
    # EX	existential there
    # FW	foreign word (ante, de)
    # IN	preposition (on, of)
    # LS	List item marker
    # MD	modal auxiliary (might, will)
    # PDT	determiner, pre- (all, both, half)
    # POS	possessive particle (', 's)
    # RP	adverbial particle (back, up)
    # SENT	sentence-final punctuation (.)
    # SYM	symbol or formula (US$500, R300)
    # TO	infinitive marker (to)
    # UH	interjection (aah, oh, yes, no)


    @staticmethod
    def _pos_pos_map(pos):
        if re.match('^V', pos):
            return 'V'

        elif re.match('^(N|EX|PP|W)', pos):
            return 'N'

        elif re.match('^JJ', pos):
            return 'Adj'

        elif re.match('^RB', pos):
            return 'Adv'

        elif re.match('^IN', pos):
            return 'P'

        elif re.match('^RP', pos):
            return 'Part'

        elif re.match('^DT', pos):
            return 'D'

        elif re.match('^CD', pos):
            return 'Num'

    @staticmethod
    def _word_filter(lemma):
        return lemma
        try:
            ## filter things not in the US or UK dictionaries
            if D_US.check(lemma) or D_GB.check(lemma):
                return lemma
            else:
                raise ValueError, 'word misspelled'
        except:
            raise ValueError, 'invalid character in sentence'


    def __init__(self, sentence, word, lemma, pos, relation, index, validate=True):
        self.sentence = sentence
        self.word = word
        self.lemma = lemma
        self.pos = pos
        self.index = index
        self.relation = relation

        self.embedded_index = None
        self.highest_index = 0

        self._extract_information()

        self._validate_information(validate)

    def __getitem__(self, key):
        return self.__dict__[key]

    def get_data(self, datahead):
        line = []

        for head in datahead:
            try:
                val = self.__dict__[head].lower()
                val = WordInformation._word_filter(val)
                line.append(val)
            except KeyError:
                line.append('NONE')

        return line
        

class VerbInformation(WordInformation):

    # VB	be    base (be)
    # VBD	be    past tense (went)
    # VBG	be    -ing (being)
    # VBN	be    past participle (been)
    # VBP	be    plural (are)
    # VBZ	be    -s (is)
    # VH	have  base (have)
    # VHD	have  past tense (had)
    # VHG	have  -ing (having)
    # VHN	have  past participle (had)
    # VHP	have  plural (have)
    # VHZ	verb  -s (believes)
    # VV	verb  base (believe)
    # VVD	verb  past tense (believed)
    # VVG	verb  -ing (believing)
    # VVN	verb  past participle (believed)
    # VVP	verb  plural (believe)
    # VBZ	verb  -s (believes)

    return_params = {'return_lemma'    : True,
                     'return_pos'      : True,
                     'return_index'    : True,
                     'return_relation' : True}

    @staticmethod
    def _pos_tense_map(pos):
        if re.match('V.D', pos):
            return 'past'

        elif re.match('V.G', pos):
            return 'gerund'

        elif re.match('V.N', pos):
            return 'pastpart'
        
        elif re.match('V.P', pos):
            return 'present'

        elif re.match('V.Z', pos):
            return 'present'

        else:
            return 'nil'        

    def _extract_information(self):
        self._initialize_values()

        self._extract_dependent_information(self.index)        
        self._extract_parent_information()

    def _validate_information(self, validate):
        if validate:
            try:
                self._validate_aux_chain()
                self._validate_matrix()
                self._validate_embedded()
                self._validate_arguments()       
            except Exception as e:
                raise

    def _initialize_values(self):
        self.tense = VerbInformation._pos_tense_map(self.pos)

        self.matrix = 'false'
        self.to = 'false'

        self.object_counter = 0
        self.prep_counter = 0
        #self.adverb_counter = 0
        
    def _extract_aux_information(self, lemma, pos):
        tense = VerbInformation._pos_tense_map(pos)

        ## if the main verb parent is have
        if re.match('^VH', pos):
            self.have = tense
            return 'have'

        ## if the main verb parent is be
        if re.match('^VB', pos):
            self.be = tense
            return 'be'

        ## if the main verb parent is a modal
        elif re.match('^MD', pos):
            self.modal = lemma
            return 'modal'

        ## if the tense is instantiated by a "do" aux
        elif lemma == 'do':
            ## set the matrix tense to the tense of "do"
            self.tense = tense
            return 'do'

    def _extract_dependent_information(self, index):
        dependents = self.sentence.get_dependents(index=index, 
                                                  **VerbInformation.return_params).next()

        for d_lem, d_pos, d_ind, d_rel in dependents:
            if d_pos == 'TO':
                self.to = 'true'

            self._extract_nonverb_dependent_information(lemma=d_lem, 
                                                        pos=d_pos, 
                                                        index=d_ind, 
                                                        relation=d_rel)
        
            self._extract_complementizer(lemma=d_lem, 
                                         pos=d_pos, 
                                         index=d_ind)

            if index == self.index:
                if re.match('^V', d_pos):
                    if d_rel == 'OBJ':
                        self.embedded_index = d_ind
                    elif d_rel == 'VC':
                        raise ValueError, 'this verb is in the middle of an aux chain'                


    def _extract_nonverb_dependent_information(self, lemma, pos, index, relation):
        self._extract_noun_information(lemma, pos, relation)
        self._extract_adjective_information(lemma, pos, relation)
        self._extract_preposition_information(index, lemma, pos)

    def _extract_parent_information(self):
        index, relation, tense = self.index, self.relation, self.tense

        ## move through three levels of embedding
        ## will get largest aux chains: 
        ## ((MOD, LEXICAL) (HAVE) (BE), DO) (VERB)
        for i in range(3):
            self.highest_index = index                

            if 'be' in self.__dict__:
                if self.tense == 'past':
                    self.tense = 'pastpart'
            
            if 'have' in self.__dict__:
                if self.tense == 'past':
                    self.tense = 'pastpart'
                if 'be' in self.__dict__:
                    if self.be == 'past':
                        self.be = 'pastpart'

            if relation == 'ROOT':
                self.matrix = 'true'

                if self.tense == 'nil' and index == self.index:
                    if 'modal' not in self.__dict__:
                        self.tense = 'present'

                break

            ## get the next highest element (parent)
            p_lem, p_pos, p_ind, p_rel = self.sentence.get_parent(index=index, 
                                                                  **VerbInformation.return_params).next()           
            aux = self._extract_aux_information(lemma=p_lem, pos=p_pos)

            ## if it was an aux, look at its dependents
            if aux:
                self._extract_dependent_information(p_ind)
            ## otherwise, we're done
            else:
                break

            ## if you made it this far, reset the current element to the current parent
            index, relation = p_ind, p_rel


    def _extract_noun_information(self, lemma, pos, relation):
        if re.match('^(N|PP|EX|W)', pos):
            if relation == 'SBJ':
                self.subject = lemma

            elif relation == 'OBJ':
                self.object_counter += 1
                key = 'object'+str(self.object_counter)
                self.__dict__[key] = lemma

            elif relation == 'PRD':
                self.predicate = lemma
                self.predclass = 'N'

    def _extract_adjective_information(self, lemma, pos, relation):
        if re.match('^JJ', pos):
            if relation == 'PRD':
                self.predicate = lemma
                self.predclass = 'Adj'

    def _extract_preposition_information(self, index, lemma, pos):
        if re.match('^IN', pos):
            if lemma not in ['if', 'that', 'whether']:
                self.prep_counter += 1
                prep_key = 'prep'+str(self.prep_counter)
                prepobj_key = 'prep'+str(self.prep_counter)+'object'

                ## check all its dependents
                dependents = self.sentence.get_dependents(index=index, 
                                                          return_lemma=True, 
                                                          return_pos=True,
                                                          return_index=True).next()

                for dep_lemma, dep_pos, dep_index in dependents:
                    if re.match('^(N|PP|EX|W)', dep_pos):
                        self.__dict__[prep_key] = lemma
                        self.__dict__[prepobj_key] = dep_lemma

                    elif re.match('^IN', dep_pos):
                        dependents2 = self.sentence.get_dependents(index=dep_index, 
                                                                   return_lemma=True, 
                                                                   return_pos=True).next()
                        for dep2_lemma, dep2_pos in dependents2:
                            if re.match('^(N|PP|EX|W)', dep_pos):
                                self.__dict__[prep_key] = lemma + '_' + dep_lemma
                                self.__dict__[prepobj_key] = dep2_lemma
                else:
                    if 'prep_key' not in self.__dict__.keys():
                        self.__dict__[prep_key] = lemma
        
        elif re.match('^RP', pos):
            self.particle = lemma

    def _extract_complementizer(self, lemma, pos, index):
        dependents = self.sentence.get_dependents(index=index, 
                                                  return_lemma=True, 
                                                  return_pos=True).next()


        ## if the word is a licit complementizer 
        ## and the POS is preposition
        if lemma in ['if', 'that', 'whether', 'like', 'for']  and pos == 'IN':
            if int(index) < int(self.index):
                if dependents.shape[0] == 0:
                    self.complementizer = lemma
            

        ## if the word is a WH and doesn't contain "ever"
        elif 'ever' not in lemma and re.match('^W', pos):
            self.complementizer = lemma

        ## if the word is a noun
        elif re.match('^(N|PP|EX|W)', pos):
            for dep_lemma, dep_pos in dependents:
                ## for a WH that is not free choice
                if 'ever' not in dep_lemma and re.match('^W', dep_pos):
                    self.complementizer = dep_lemma

    def _validate_aux_chain(self):
        try:
            self._validate_be_chain()
            self._validate_have_chain()
            self._validate_modal_chain()

        except AssertionError:
            raise ValueError, 'invalid aux chain'

    def _validate_be_chain(self):
        if 'be' in self.__dict__.keys():
            assert self.tense in ['pastpart', 'gerund', 'nil']

    def _validate_have_chain(self):
        if 'have' in self.__dict__.keys():
            if 'be' in self.__dict__.keys():
                assert self.be in ['pastpart', 'nil'] ## have to allow 'nil' for "have to"
            else:
                assert self.tense in ['pastpart', 'nil'] ## have to allow 'nil' for "have to"

    def _validate_modal_chain(self):
        if 'modal' in self.__dict__.keys():
            if 'have' in self.__dict__.keys():
                assert self.have == 'nil'
            elif 'be' in self.__dict__.keys():
                assert self.be == 'nil'
            else:
                assert self.tense == 'nil'

    def _validate_matrix(self):
        try:
            if self.matrix == 'true':
                assert 'subject' in self.__dict__.keys()
                assert self.to == 'false'

                if 'complementizer' in self.__dict__.keys():
                    assert self.complementizer not in ['that', 'if', 'whether', 'like', 'for']

        except AssertionError:
            raise ValueError, 'invalid matrix clause'

    def _validate_embedded(self):
        try:
            if self.matrix == 'false':
                if self.to == 'true':
                    if 'have' in self.__dict__.keys():
                        assert self.have == 'nil'
                    elif 'be' in self.__dict__.keys():
                        assert self.be == 'nil'
                    else:
                        assert self.tense == 'nil'

                if self.tense not in ['nil', 'gerund', 'pastpart']:
                    assert 'subject' in self.__dict__.keys()

                if 'complementizer' in self.__dict__.keys():
                    if self.to == 'true':
                        assert self.complementizer not in ['that', 'if', 'like']

                    if self.complementizer == 'for':
                        assert self.to == 'true'

        except AssertionError:
            raise ValueError, 'invalid embedded clause'

    def _validate_arguments(self):
        for prep in ['prep1', 'prep2', 'prep3']:
            if prep in self.__dict__.keys():
                if 'be' not in self.__dict__.keys() or self.tense != 'pastpart':
                    assert self.__dict__[prep] != 'by'
            

if __name__ == '__main__':

    corpus = Corpus(sys.argv[1])

    sentence_information = tree()

    ## run through each document in the corpus
    for i, doc in enumerate(corpus):
        ## run through each sentence in the document
        for j, sent in enumerate(doc):
            ## create a generator for lemmatized verbs, their part of speech, 
            ## and their relation to their parent

            try:
                sent_info = SentenceInformation(sent)

                sentence_information[i][j] = sent_info

            except ValueError as e:
                pass
