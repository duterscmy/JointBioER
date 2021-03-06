# -*- coding: utf-8 -*-


import codecs as cs
import re
from utils import SaveGoldEntity,SaveGoldRelation,sample_token4
import nltk

#一些用到的字典
small =  {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}
eAbbr = {'CHEMICAL':'chem','GENE-Y':'geneY','GENE-N':'geneN'}
RelationAbbr = {'CPR:3':'C3','CPR:4':'C4','CPR:5':'C5','CPR:6':'C6','CPR:9':'C9'}

if_repeat = 'Y'
pattern = 'test'#train or test or vaild
if pattern == 'train':
    abdir = '../../ChemProt_Corpus/chemprot_train_new/chemprot_training_abstracts.tsv'
    edir = '../../ChemProt_Corpus/chemprot_train_new/chemprot_training_entities.tsv'
    rdir = '../../ChemProt_Corpus/chemprot_train_new/chemprot_training_relations.tsv'
    outdir = '../data/CPR_%s_%s.txt'%(pattern,if_repeat)
    goldedir = '../data/goldEntityAnswer_%s.txt'%(pattern)
    goldrdir = '../data/goldRelationAnswer_%s.txt'%(pattern)
elif pattern == 'vaild':
    abdir = '../../ChemProt_Corpus/chemprot_development_new/chemprot_development_abstracts.tsv'
    edir = '../../ChemProt_Corpus/chemprot_development_new/chemprot_development_entities.tsv'
    rdir = '../../ChemProt_Corpus/chemprot_development_new/chemprot_development_relations.tsv'
    outdir = '../data/CPR_%s_%s.txt'%(pattern,if_repeat)
    goldedir = '../data/goldEntityAnswer_%s.txt'%(pattern)
    goldrdir = '../data/goldRelationAnswer_%s.txt'%(pattern)
elif pattern == 'test':
    abdir = '../../ChemProt_Corpus/chemprot_test_gs/chemprot_test_abstracts_gs.tsv'
    edir = '../../ChemProt_Corpus/chemprot_test_gs/chemprot_test_entities_gs.tsv'
    rdir = '../../ChemProt_Corpus/chemprot_test_gs/chemprot_test_relations_gs.tsv'
    outdir = '../data/CPR_%s_%s.txt'%(pattern,if_repeat)
    goldedir = '../data/goldEntityAnswer_%s.txt'%(pattern)
    goldrdir = '../data/goldRelationAnswer_%s.txt'%(pattern)
    
#读入abstract
fp = cs.open(abdir,'r','utf-8')
text = fp.read().split('\n')[:-1]
fp.close()

#读入所有实体，dic, key为文章号，值为list，列表的元素为实体信息list [实体序号，实体类型，左边界，右边界，实体名]
fp1 = cs.open(edir,'r','utf-8')
entitys = fp1.read().split('\n')[:-1]
fp1.close()
edic = {}
for line in entitys:
    #
    elements = line.split('\t')
    id = elements[0]
    if id in edic:
        edic[id].append([elements[1],elements[2],int(elements[3]),int(elements[4]),elements[5]])
    else:
        edic[id] = []
        edic[id].append([elements[1],elements[2],int(elements[3]),int(elements[4]),elements[5]])

#读入所有关系，dic, key为文章号，值为list，列表的元素为实体信息list [关系group，是否正例，细分类别，实体1序号，实体2序号]
fp2 = cs.open(rdir,'r','utf-8')
relations = fp2.read().split('\n')[:-1]
fp2.close()
rdic = {}
for line in relations:
    elements = line.split('\t')
    id = elements[0]
    if id in rdic:
        rdic[id].append([elements[1],elements[2],elements[3],elements[4][5:],elements[5][5:]])
    else:
        rdic[id] = []
        rdic[id].append([elements[1],elements[2],elements[3],elements[4][5:],elements[5][5:]])
#剔除掉有复合实体参与的关系

#from GetNoFuheRelation import GetNoRelation
#rdic = GetNoRelation(pattern)
'''
仿照ddi数据的格式，生成senlist
senlist是存放整个数据集的list,每个元素是一个句子对应的字典，键分别为entity pair text,值为对应的列表和字符串
'''
max_len = 0
all_len = 0
Senslist = []
for line in text:
    article_id = line.split('\t')[0]
    abstract = line.split('\t')[1]
    text = line.split('\t')[2]
    #切分句子
    sentences = []
    for s in text.split('. '):
        if s[0] in small and len(sentences)>0:#如果该句的开头是小写字母，且前面有句子，则拼接到上一个句子中
            sentences[-1] = sentences[-1] + s + '. '
        else:#否则该句单独作为一个句子
            sentences.append(s + '. ')
    sentences[-1] = sentences[-1][:-2]#最后一句话无需加上". "
    sens = []
    sens.append(abstract+' ')
    sens.extend(sentences)
    #统计句子最大长度
    
    for each in sens:
        all_len += len(each)
        if len(each)>max_len:
            #print each
            max_len = len(each)
    #得到每个句子的起止位置
    sens_len = []
    begin = 0
    end = 0
    for i in range(len(sens)):
        end = begin + len(sens[i])
        sens_len.append([begin,end])
        begin = end
    #对于文章里每个句子的起始位置，得到属于该句子的所有实体和关系
    rnum = 0
    for i in range(len(sens_len)):
        sendic = {}#存放一个句子的文本、实体、关系
        sendic['text'] = sens[i]
        sendic['entity'] = []
        sendic['pair'] = []
        begin = sens_len[i][0]
        end = sens_len[i][1]

        sen_e_index = []#该句子的所有实体在文章中的序号
        #取出属于该句子的实体
        for e in edic[article_id]:
            if e[2] >= begin and e[3] <= end:
                sendic['entity'].append([e[2]-begin,e[3]-begin-1,e[1]])#实体位置改为含头含尾
                sen_e_index.append(e[0])
        #得到该句子的关系
        if article_id in rdic:#如果该文章是包含关系的
            for r in rdic[article_id]:
                if r[1] == u'Y ':#Y后有空格
                    e1 = r[3]
                    e2 = r[4]
                    if e1 in sen_e_index and e2 in sen_e_index:
                        e1_index = sen_e_index.index(e1)
                        e2_index = sen_e_index.index(e2)
                        sendic['pair'].append([e1_index,e2_index,r[0]])
                        rnum +=1
        
        Senslist.append(sendic)
print 'max sentence length is %s'%(max_len)
print 'average length is %.2f'%(float(all_len)/len(Senslist))


def ChangeIndex(senslist):#将实体位置调整为忽略空格的位置
    for sentence in senslist:#每个句子：字典
        text = sentence['text']#取出文本
        while(' ' in text):#当文本中有空格时
            for i in range(len(text)):#i即为当前第一个空格空格出现的位置
                if text[i] == ' ':
                    break
            for entity in sentence['entity']:#句子中的每个实体 [left,right,label]
                if entity[0] > i:#如果该实体在空格后面，则将它的左右边界同时减一
                    entity[0] -= 1
                    entity[1] -= 1
                if entity[0] < i and entity[1] > i:#如果该实体包含空格，则将它的右边界减一
                    entity[1] -= 1
            text = text[0:i] + text[i+1:]
    
def GenarateBIO(senslist, schema):#生成BIO标注的二维list
    article = []#文章级别的列表
    token_more_than_entity = 0
    for i in range(len(senslist)):
        text = senslist[i]['text']#取出文本
        text = sample_token4(text)
        text = nltk.tokenize.word_tokenize(text)
        entitys = senslist[i]['entity']
        word_label = []#句子级别的列表
        left = -1
        right = -1
        for token in text:
            left = right + 1#当前token的左右边界（含头含尾）
            right = right + len(token)
            ifBI = 0
            if schema == 'BIOES':
                for entity in entitys:
                    #先使用类别为chemical的标记token,再使用gene覆盖掉
                    if entity[2] == 'CHEMICAL':
                        if left == entity[0] and right == entity[1] :
                            now_token = [token,'S-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left == entity[0] and right < entity[1]:
                            now_token = [token,'B-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left > entity[0] and right < entity[1]:
                            now_token = [token,'I-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left > entity[0] and right == entity[1]:
                            now_token = [token,'E-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left == entity[0] and right > entity[1]:
                            now_token = [token,'S-'+eAbbr[entity[2]]]
                            ifBI = 1
    #                        print token
    #                        print entity[0],entity[1]
    #                        print left,right
    #                        print entitys
    #                        print senslist[i]['text']
    #                        print senindex2file[i] +'\n'
                            token_more_than_entity += 1
                            #print 'token length more than entity length'
                            #break
                for entity in entitys:
                    if entity[2] == 'GENE-Y' or entity[2] == 'GENE-N':
                        if left == entity[0] and right == entity[1] :
                            now_token = [token,'S-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left == entity[0] and right < entity[1]:
                            now_token = [token,'B-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left > entity[0] and right < entity[1]:
                            now_token = [token,'I-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left > entity[0] and right == entity[1]:
                            now_token = [token,'E-'+eAbbr[entity[2]]]
                            ifBI = 1
                            #break
                        elif left == entity[0] and right > entity[1]:
                            now_token = [token,'S-'+eAbbr[entity[2]]]
                            ifBI = 1
                            token_more_than_entity += 1
                if ifBI == 0:
                    now_token = [token,'O']
                word_label.append(now_token)
        article.append(word_label) 
    print 'there is %s token length > entity'%token_more_than_entity
    return article
    
def AddRelation(senslist,token2BIOES):#实体可能有重复的关系
    for i in range(len(senslist)):#对于每句话
        pairs = senslist[i]['pair']#取出关系
        entitys = senslist[i]['entity']
        if len(pairs) == 0:
            continue
        for pair in pairs:#对于每个关系
            e1_index = pair[0]#实体1在句子中的索引
            e2_index = pair[1]#实体2在句子中的索引
            label = pair[2]#关系
            e1_dir = entitys[e1_index][:2]#实体1的左右边界（忽略空格）
            e2_dir = entitys[e2_index][:2]#实体2的左右边界（忽略空格）
            labelAbbr = RelationAbbr[label]#该关系的缩写
            left = -1
            right = -1
            for token in token2BIOES[i]:#遍历句子中的每个token
                left = right + 1#当前token的左右边界（含头含尾）
                right = right + len(token[0])
                if len(token) == 2:#如果之前没包含类别的标签
                    if left >= e1_dir[0] and right <= e1_dir[1]:
                        token.append('%s-%s-1'%(token[1],labelAbbr))
                    if left >= e2_dir[0] and right <= e2_dir[1]:
                        token.append('%s-%s-2'%(token[1],labelAbbr))
                elif len(token) > 2:
                    before_token_label = token[-1].split('-')[2]
                    before_token_dir = token[-1].split('-')[3]
                    if left >= e1_dir[0] and right <= e1_dir[1]:
                        if labelAbbr != before_token_label:
                            now_token_label = 'MU'
                        else:
                            now_token_label = labelAbbr
                        if before_token_dir != '1':
                            now_token_dir = 'M'
                        else:
                            now_token_dir = '1'
                        token.append('%s-%s-%s'%(token[1],now_token_label,now_token_dir))
                    
                    if left >= e2_dir[0] and right <= e2_dir[1]:   
                        if labelAbbr != before_token_label:
                            now_token_label = 'MU'
                        else:
                            now_token_label = labelAbbr
                        if before_token_dir != '2':
                            now_token_dir = 'M'
                        else:
                            now_token_dir = '2'
                        token.append('%s-%s-%s'%(token[1],now_token_label,now_token_dir))
    return token2BIOES

def AddRelation2(senslist,token2BIOES):#实体无重复的关系
    for i in range(len(senslist)):#对于每句话
        pairs = senslist[i]['pair']#取出关系
        entitys = senslist[i]['entity']
        if len(pairs) == 0:#如果这句话没有关系，则跳过
            continue
        relatedEn = []#这句话中存在关系的实体的索引
        for pair in pairs:#对于每个关系
            e1_index = pair[0]#实体1在句子中的索引
            e2_index = pair[1]#实体2在句子中的索引
            if e1_index in relatedEn or e2_index in relatedEn:#判断这两个实体是否已存在关系
                continue
            else:#若不存在，则将他们标记为已存在关系，进行进一步操作
                relatedEn.append(e1_index)
                relatedEn.append(e2_index)
            label = pair[2]#关系
            e1_dir = entitys[e1_index][:2]#实体1的左右边界（忽略空格）
            e2_dir = entitys[e2_index][:2]#实体2的左右边界（忽略空格）
            labelAbbr = RelationAbbr[label]#该关系的缩写
            left = -1
            right = -1
            for token in token2BIOES[i]:#遍历句子中的每个token
                left = right + 1#当前token的左右边界（含头含尾）
                right = right + len(token[0])
                if left >= e1_dir[0] and right <= e1_dir[1]:
                    token.append('%s-%s-1'%(token[1],labelAbbr))
                if left >= e2_dir[0] and right <= e2_dir[1]:
                    token.append('%s-%s-2'%(token[1],labelAbbr))
#        if len(token2BIOES[i])==0 or len(token2BIOES[i])==1:
#            print files[i]
    return token2BIOES

def GetGoldAnwer(SentencesList):#保存标注的ytest的实体位置和关系位置/类别
    gold_entity = []#所有实体的位置
    gold_relation = []#所有关系的实体位置及类别
    for sentence in SentencesList:#每句话
        text = sentence['text']
        text = sample_token4(text)
        text = nltk.tokenize.word_tokenize(text)

        entity_s = []#一句话中的实体
        relation_s = []#一句话中的关系
        for entity in sentence['entity']:#将这句话中实体们的位置保存
            entity_s.append([entity[0],entity[1],eAbbr[entity[2]]])
        for pair in sentence['pair']:
            e1_index = pair[0]#实体1在句子中的索引
            e2_index = pair[1]#实体2在句子中的索引
            label = pair[2]#关系
            e1_dir = sentence['entity'][e1_index][:2]#实体1的左右边界（忽略空格）
            e2_dir = sentence['entity'][e2_index][:2]#实体2的左右边界（忽略空格）
            labelAbbr = RelationAbbr[label]#该关系的缩写
            relation_s.append([e1_dir[0],e1_dir[1],e2_dir[0],e2_dir[1],labelAbbr])
        gold_entity.append(entity_s)
        gold_relation.append(relation_s)
    return gold_entity,gold_relation


ChangeIndex(Senslist)#将实体的位置改成无空格情况的位置
gold_entity,gold_relation = GetGoldAnwer(Senslist)#保存标注的实体和关系信息
SaveGoldEntity(goldedir,gold_entity)
SaveGoldRelation(goldrdir,gold_relation)
tokenandlabel= GenarateBIO(Senslist,'BIOES')#生成token：label的BIOES标签
fp = cs.open(outdir,'w','utf-8')
num_pass = 0
tokenlen_max = 0
tokenlen_ave = 0.0
numtoken = 0.0
if if_repeat == 'N':#每个token不可以存在多重关系
    tokenandlabel = AddRelation2(Senslist,tokenandlabel)
    for sentence in tokenandlabel:
        for token in sentence:#
            if len(token)==2:
                fp.write(token[0]+'\t'+token[1]+'\n')
            else:
                fp.write(token[0]+'\t'+token[2]+'\n')
        fp.write('\n')
else:#每个token可以存在多重关系,它的标签会被最后一个关系覆盖
    tokenandlabel = AddRelation(Senslist,tokenandlabel)
    for sentence in tokenandlabel:
        for token in sentence:
            fp.write(token[0])
            if len(token[0])>tokenlen_max:
                tokenlen_max = len(token[0])
            numtoken += 1
            tokenlen_ave += len(token[0])
            if len(token) == 2:
                fp.write('\t'+token[1])
            else:
                fp.write('\t'+token[-1])
            fp.write('\n')
        fp.write('\n')
fp.close()
print 'max token length = %d'%tokenlen_max
print 'average token length = %.2f'%(tokenlen_ave/numtoken)
print 'new corpus!!!'
##查看由于标签产生的关系错误的
#from GenerateXY import GetXY
#from utils import label2answer,loadtokens,computeFr,computeFr_2
#testtokens = loadtokens(u'../data/CPR_test_Y.txt')
#xtest,y_test,xctest= GetXY(u'../data/CPR_test_Y.txt',mask = 0)
#predict_e,predict_r =label2answer(y_test,testtokens)
##for i in range(len(gold_relation)):
##    if cmp(gold_relation[i], predict_r[i])!= 0 and len(gold_relation[i])!= len(predict_r[i]):
##        print testtokens[i]
##        print gold_relation[i],predict_r[i]
##        print '\n'
#pr,rr,fr,frlabel = computeFr(gold_relation,predict_r)
#r1,r2 = computeFr_2(gold_relation,predict_r)
#print u'由goldy得到的关系的PRF为%f %f %f'%(pr,rr,fr)