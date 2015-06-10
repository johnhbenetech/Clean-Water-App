#_*_ coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse
import sys
import os
import requests
import json
import zipfile
from io import BytesIO
import StringIO
import xlsxwriter
import datetime
from urllib2 import urlopen

# Index displays the data on the first page
def index(request, login_name):
    
    if login_name == "adamb":
        FHLogin = "adamb"
        FHPass = "cleanwaterpass"
        FHServer = "http://54.86.146.199"
        headers = {'Authorization':'Token 16d24bfe6de3e4c2c35dd68f8dc4d45cb62c16f4'}
    elif login_name == "cleanwatercr":
        FHLogin = "cleanwatercr"
        FHPass = "cleanwaterpass"
        FHServer = "http://formhub.org"
        headers = {'Authorization':'Token b67eed4084407b53ad32e7277fbb68ecbcf31515'}
        print "hello world"
        
    url = FHServer + "/api/v1/forms/" + FHLogin
    
    result = requests.get(url, headers=headers)
    surveyData = json.loads(result.content)
    
    surveyDict = {}
    
    if surveyData:
        print surveyData
        for x in range(0, len(surveyData)):
            dataDict = {}
            dataDict['url'] = surveyData[x]['url']
            dataDict['date_created'] = surveyData[x]['date_created']
            dataDict['formid'] = surveyData[x]['formid']
            dataDict['last_submission_time'] = surveyData[x]['last_submission_time']
            dataDict['num_of_submissions'] = surveyData[x]['num_of_submissions']
            dataDict['login_name'] = FHLogin
            
            surveyDict[surveyData[x]['title']] = dataDict
                     
    context = {'surveys': surveyDict}    
    return render(request, 'water_data/index.html', context)
    #return HttpResponse("hello world", mimetype='application/json')
    
  
def listSubmissions(request, survey_id, login_name, survey_title):  
    
    if login_name == "adamb":
        FHLogin = "adamb"
        FHPass = "cleanwaterpass"
        FHServer = "http://54.86.146.199"
        headers = {'Authorization':'Token 16d24bfe6de3e4c2c35dd68f8dc4d45cb62c16f4'}
        
    url = FHServer + "/api/v1/data/" + FHLogin + "/" + survey_id
    full_url = request.build_absolute_uri(None)
    
    result = requests.get(url, headers=headers)
    surveyData = json.loads(result.content)
   
    surveyDict = {}
    
    if surveyData:
        for x in range(0, len(surveyData)):
            dataDict = {}
            dataDict['submission_time'] = surveyData[x]['_submission_time']     
            dataDict['submission_id'] = surveyData[x]['_id']       
            surveyDict[surveyData[x]['personalization_group/personalization_question_3']] = dataDict
      
    context = {'surveys': surveyDict, 'title': survey_title, 'url' : full_url}    
    return render(request, 'water_data/listSubmissions.html', context)     
    
    
def xlsDownload(request, survey_id, login_name, survey_title, submission_id):   
    
    output = StringIO.StringIO()
    
    if login_name == "adamb":
        FHLogin = "adamb"
        FHPass = "cleanwaterpass"
        FHServer = "http://54.86.146.199"
        headers = {'Authorization':'Token 16d24bfe6de3e4c2c35dd68f8dc4d45cb62c16f4'}
    
    #JSON requests for survey questions/answers
    urlAnswers = FHServer + "/api/v1/data/" + FHLogin + "/" + survey_id
    urlQuestions = FHServer + "/api/v1/forms/" + FHLogin + "/" + survey_id + "/" + "form.json"
       
    headers = {'Authorization':'Token 16d24bfe6de3e4c2c35dd68f8dc4d45cb62c16f4'}
    result = requests.get(urlAnswers, headers=headers)
    dataAnswers = json.loads(result.content)
    result = requests.get(urlQuestions, headers=headers)
    dataQuestions = json.loads(result.content)
    
    #extract survey questions, put them in dictionary
    #format: communication_question_1, {question:“question”, answer:“answer”}

    #list of all the groups to be analyzed in dashboard
    groups = ['personalization', 'community', 'administration', 'operation', 'sanitation', 'education_sanitation', 'GIRH', 'GIRS', 'communication']
    questionDict = {}

    for x in range (2, 11):
        for data in dataQuestions['children'][x]['children']:
            answerDict = {}
            answerDict['question'] = data['label']
            questionDict[data['name']] = answerDict     


    #------------------------------------------
    #------------------------------------------
    #------------------------------------------

    #start for loop here to iterate through responses
    #at some point we need to clear the dictionary to re-up it
    for responseNum in range(0, len(dataAnswers)):
        if (str(dataAnswers[responseNum]['_id']) == str(submission_id)):
  
            resultsDict = dataAnswers[responseNum]

            #edit resultsDict to have trimmed keys
            tempResultsDict = {}

            for key,value in resultsDict.iteritems():
                if "submission_time" in key:
                    submissionDate = resultsDict[key]
                if "/" in key:
                    tempResultsDict[key.split("/")[1]] = resultsDict[key]

            resultsDict = tempResultsDict

            #combine questionDict and resultsDict
            for key,value in questionDict.iteritems():
                result = resultsDict.get(key)
                if (result):
                    #update answerDict in questionDict w/ results
                    answerDict = questionDict[key]
                    answerDict['answer'] = result
                    questionDict[key] = answerDict
                else: #groups that aren't filled out get an answer of 'n/a
                    answerDict = questionDict[key]
                    answerDict['answer'] = 'n/a'
                    questionDict[key] = answerDict

            #Setup XLS file
            #-----------------------------------
            OCSA_name = questionDict.get('personalization_question_3')['answer']         
            #workbook = xlsxwriter.Workbook(OCSA_name + '.xlsx')
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheetData = workbook.add_worksheet('Data')

            #Cell formatting Data section
            #-----------------------------------
            formatWhite = workbook.add_format({'border': True, 'text_wrap' : True})
            formatWhiteBold = workbook.add_format({'border': True, 'text_wrap' : True, 'bold' : True})
            formatCenter = workbook.add_format({'border': True, 'text_wrap' : True, 'align' : 'center'})
            formatRight = workbook.add_format({'border': True, 'text_wrap' : True, 'align' : 'right'})
            formatCenterBoldUnderline = workbook.add_format({'border': True, 'text_wrap' : True})

            formatPersonalization = workbook.add_format({'bg_color':'#FF0000', 'border': True, 'bold' : True})
            formatCommunity = workbook.add_format({'bg_color':'#FFFF00', 'border': True, 'bold' : True})
            formatAdministration = workbook.add_format({'bg_color':'#92D050', 'border': True, 'bold' : True})
            formatOperation = workbook.add_format({'bg_color':'#00B0F0', 'border': True, 'bold' : True})
            formatSanitation = workbook.add_format({'bg_color':'#FFC000', 'border': True, 'bold' : True})
            formatEducation = workbook.add_format({'bg_color':'#C00000', 'border': True, 'bold' : True})
            formatGIRH = workbook.add_format({'bg_color':'#B1A0C7', 'border': True, 'bold' : True})
            formatGIRS = workbook.add_format({'bg_color':'#D8E4BC', 'border': True, 'bold' : True})
            formatCommunication = workbook.add_format({'bg_color':'#948A54', 'border': True, 'bold' : True})

            #cell formatting Interpretation section
            formatRed = workbook.add_format({'bg_color':'#FF0000', 'border': True, 'bold' : False, 'text_wrap' : True, 'align' : 'center'})
            formatOrange = workbook.add_format({'bg_color':'#F79646', 'border': True, 'bold' : False, 'text_wrap' : True, 'align' : 'center'})
            formatYellow = workbook.add_format({'bg_color':'#FFFF00', 'border': True, 'bold' : False, 'text_wrap' : True, 'align' : 'center'})
            formatGreen = workbook.add_format({'bg_color':'#00B050', 'border': True, 'bold' : False, 'text_wrap' : True, 'align' : 'center'})
            formatPercentage = workbook.add_format({'num_format': '0%', 'border': True, 'bold' : False, 'text_wrap' : True, 'align' :'right'})
            formatSpacer = workbook.add_format({'bg_color':'#538DD5', 'border': False, 'bold' : False, 'text_wrap' : True, 'align' : 'center'})

            formats = [formatPersonalization, formatCommunity, formatAdministration, formatOperation, formatSanitation, formatEducation, formatGIRH, formatGIRS, formatCommunication]

            #set column sizes
            worksheetData.set_column(0, 0, 10)
            worksheetData.set_column(1, 1, 50)
            worksheetData.set_column(2, 2, 30)
            worksheetData.set_column(3, 3, 20)

            #-----------------------------------

            row = 0
            col = 0

            groupSizeList = [] #size of each group
            groupNames = [] #names of each group
            groupScores = [] #score of each group
            groupFilledList = [] #list of bools whether a group has been filled out

            #iterate through groups
            for groupNum in range(0, len(groups)): #should be 9
                groupScore = 0
                groupSize = 0

                #determine the number of questions in each group
                for key,value in questionDict.iteritems():
                    if groups[groupNum] + '_question_' in key:
                        if groups[groupNum] == "sanitation":    #if group is sanitation
                            if key.split("_")[0] == "sanitation":   #then only add sanitation, not education_sanitation
                                groupSize += 1
                        else:   #default case
                            groupSize += 1

                #record # of questions in each list for viz
                groupSizeList.append(groupSize)

                #Write Personalization header to XLS
                if groupNum == 0:
                    worksheetData.write(row, col, '#', formats[groupNum])
                    worksheetData.write(row, col + 1, u'PERSONALIZACIÓN', formats[groupNum])
                    worksheetData.merge_range('C' + str(row + 1) + ':D' + str(row + 1),'REPUESTAS', formats[groupNum])

                    row += 1

                    #Write answers to Personalization group to XLS
                    for x in range (1, groupSize+1):
                        outputQuestion = questionDict.get(groups[groupNum] + '_question_' + str(x))
                        if(outputQuestion):
                            worksheetData.write(row, col, outputQuestion.get('question').split(' ')[0], formatWhite)
                            worksheetData.write(row, col + 1, outputQuestion.get('question'), formatWhite)
                            worksheetData.merge_range('C' + str(row + 1) + ':D' + str(row + 1),outputQuestion.get('answer'), formatWhite)
                            row += 1

                    row += 1

                #Case for rest of groups
                else:
                    #Write header to XLS
                    worksheetData.write(row, col, '#', formats[groupNum])
                    groupTitle = questionDict.get(groups[groupNum] + '_note') 

                    if(groupTitle):
                        worksheetData.write(row, col + 1, groupTitle.get('question'), formats[groupNum])
                        #groupsName list for viz section
                        groupNames.append(groupTitle.get('question'))
                    worksheetData.write(row, col + 2, 'OBSERVACIONES / COMENTARIOS', formats[groupNum])
                    worksheetData.write(row, col + 3, u'CALIFICACIÓN', formats[groupNum])

                    row += 1
                    #write out the rest of the groups scores
                    for x in range (1, groupSize+1): ###
                        outputQuestion = questionDict.get(groups[groupNum] + '_question_' + str(x))
                        outputComment = questionDict.get(groups[groupNum] + '_comment_' + str(x))

                        if (outputQuestion):
                            worksheetData.write(row, col, outputQuestion.get('question').split(' ')[0], formatWhite)
                            worksheetData.write(row, col + 1, outputQuestion.get('question'), formatWhite)

                            #handle n/a response
                            if(outputQuestion.get('answer') != 'n/a'):
                                worksheetData.write_number(row, col + 3, float(outputQuestion.get('answer')), formatWhite)
                                groupScore += float(outputQuestion.get('answer')) #calculate total score for group
                                groupFilled = True
                            else: #if group isn't filled out = n/a, don't add to score total
                                worksheetData.write(row, col + 3, outputQuestion.get('answer'), formatWhite)
                                groupFilled = False

                        if (outputComment):
                            worksheetData.write(row, col + 2, outputComment.get('answer'), formatWhite)

                        row += 1

                    #summation for each group
                    worksheetData.write(row, col, '', formatWhite)
                    worksheetData.write(row, col + 1, 'PUNTAJE TOTAL', formatWhiteBold)
                    worksheetData.write(row, col + 2, '', formatWhite)
                    worksheetData.write_formula(row, col + 3, '=SUM(D' + str(row - groupSize + 1) + ':D' + str(row) + ')', formatWhiteBold)

                    #record groupScores and groupFilled for viz section
                    groupScores.append(groupScore)
                    groupFilledList.append(groupFilled)

                    row += 3

            #create Interpretación tab in XLS
            worksheetViz = workbook.add_worksheet(u'Interpretación')

            #set column sizes
            worksheetViz.set_column(0, 0, 5)
            worksheetViz.set_column(1, 1, 30)
            worksheetViz.set_column(2, 2, 15)
            worksheetViz.set_column(3, 3, 15)
            worksheetViz.set_column(4, 7, 15)

            row = 0
            col = 0

            #VIZ SECTION 1
            #------------------------------

            #Write header to XLS
            worksheetViz.write(row, col, '#', formatWhite)
            worksheetViz.write(row, col + 1, 'Variable', formatWhite)
            worksheetViz.write(row, col + 2, '# de preguntas', formatWhite)
            worksheetViz.write(row, col + 3, u'Puntaje Máximo de acuerdo al numero de preguntas', formatWhite)
            worksheetViz.write(row, col + 4, 'NACIENTE \n (0-30%)', formatRed)
            worksheetViz.write(row, col + 5, u'EXPANSIÓN MODERTADA \n (31-55%)', formatOrange)
            worksheetViz.write(row, col + 6, u'EXPANSIÓN AVANZADA \n (56-80%)', formatYellow)
            worksheetViz.write(row, col + 7, u'CONSOLIDACIÓN \n (81-100%)', formatGreen)


            for x in range(0, len(groups)-1): #8 because not including Personalization section
                worksheetViz.write(x + 1, col, x + 1, formatWhite)
                worksheetViz.write(x + 1, col + 1, groupNames[x], formatWhite)
                worksheetViz.write(x + 1, col + 2, groupSizeList[x+1], formatWhite)
                worksheetViz.write(x + 1, col + 3, groupSizeList[x+1]*2, formatWhite) #multiply (group size)*2 because each question is worth max 2 points

                score = float(groupScores[x])
                total = float(groupSizeList[x+1]*2)

                #for each column, follow inequality and write out score
                if (groupFilledList[x]):
                    if (score/total) <= .30:
                        worksheetViz.write(x + 1, col + 4, score, formatRed)
                    elif (score/total) > .30 and (score/total) <= .55:
                        worksheetViz.write(x + 1, col + 5, score, formatOrange)
                    elif (score/total) > .55 and (score/total) <= .80:
                        worksheetViz.write(x + 1, col + 6, score, formatYellow)
                    elif (score/total) > .80:
                        worksheetViz.write(x + 1, col + 7, score, formatGreen)


            #VIZ SECTION 2
            #------------------------------

            #write blue separator  
            row += 10
            worksheetViz.set_row(row - 1 , 3)
            worksheetViz.merge_range('A' + str(row) + ':H' + str(row), " ", formatSpacer)
            row += 2

            #write section header 
            worksheetViz.merge_range('B' + str(row + 1) + ':H' + str(row + 1), 'Puntajes', formatCenter)
            row += 1
            worksheetViz.write(row, col, '#', formatWhite)
            worksheetViz.write(row, col + 1, 'Variable', formatWhite)
            worksheetViz.write(row, col + 2, 'Puntaje', formatWhite)
            worksheetViz.write(row, col + 3, 'Porcentaje', formatWhite)
            worksheetViz.merge_range('E' + str(row + 1) + ':H' + str(row + 1), 'ETAPA', formatWhite)
            row += 1

            #write out points, percentage, and category
            totalPoints = 0 #total for all groups
            for x in range(0, len(groups)-1):
                if (groupFilledList[x]):
                    score = float(groupScores[x])
                    total = float(groupSizeList[x+1]*2)
                    totalPoints += total
                else:
                    score = "n/a" 

                #write names of groups to XLS
                worksheetViz.write(row, col, x + 1, formatWhite)
                worksheetViz.write(row, col + 1, groupNames[x], formatWhite)
                worksheetViz.write(row, col + 2, score, formatRight)


                if (groupFilledList[x]):    
                    worksheetViz.write(row, col + 3, score/total, formatPercentage)

                    #inequality to deternine category based off percentage
                    if (score/total) <= .30:
                        worksheetViz.merge_range('E' + str(row + 1) + ':H' + str(row + 1), 'NACIENTE', formatRed)
                    elif (score/total) > .30 and (score/total) <= .55:
                        worksheetViz.merge_range('E' + str(row + 1) + ':H' + str(row + 1), u'EXPANSIÓN MODERTADA', formatOrange)
                    elif (score/total) > .55 and (score/total) <= .80:
                        worksheetViz.merge_range('E' + str(row + 1) + ':H' + str(row + 1), u'EXPANSIÓN AVANZADA', formatYellow)
                    elif (score/total) > .80:
                        worksheetViz.merge_range('E' + str(row + 1) + ':H' + str(row + 1), u'CONSOLIDACIÓN', formatGreen)
                else: #case where group hasn't been filled out -> 'n/a'
                    worksheetViz.write(row, col + 3, score, formatRight)

                row += 1

            #Total line at bottom of this section
            totalAverage = sum(groupScores)/totalPoints

            worksheetViz.write(row, col + 1, 'TOTAL', formatWhite)
            worksheetViz.write_formula(row, col + 2, '=SUM(C' + str(row - len(groupScores) + 1) + ':C' + str(row) + ')', formatWhite)
            worksheetViz.write(row, col + 3, totalAverage, formatPercentage)

            row += 1

            #Inequality for category based off total score
            if (totalAverage) <= .30:
                worksheetViz.merge_range('E' + str(row) + ':H' + str(row), 'NACIENTE', formatRed)
            elif (totalAverage) > .30 and (totalAverage) <= .55:
                worksheetViz.merge_range('E' + str(row) + ':H' + str(row), u'EXPANSIÓN MODERTADA', formatOrange)
            elif (totalAverage) > .55 and (totalAverage) <= .80:
                worksheetViz.merge_range('E' + str(row) + ':H' + str(row), u'EXPANSIÓN AVANZADA', formatYellow)
            elif (totalAverage) > .80:
                worksheetViz.merge_range('E' + str(row) + ':H' + str(row), u'CONSOLIDACIÓN', formatGreen)

            row += 1

            ##write blue separator  
            worksheetViz.set_row(row-1, 3)
            worksheetViz.merge_range('A' + str(row) + ':H' + str(row), " ", formatSpacer)

            #VIZ SECTION 3 (CBar Chart)
            #------------------------------

            #format submission time
            d = datetime.datetime.strptime(submissionDate, '%Y-%m-%dT%H:%M:%S')
            submissionDateFormatted = d.strftime('%b %d, %Y')

            chart = workbook.add_chart({'type': 'column'})
            chart.set_title({'name': u'Diagnóstico \n' + str(submissionDateFormatted)})
            chart.set_size({'width': 915, 'height': 550})
            chart.set_legend({'none': True})

            #write bar chart to XLS
            chart.add_series({
                'categories': u'Interpretación!B15:B23',
                'values': u'Interpretación!D15:D23',
                'data_labels': {'value': True},
            })

            worksheetViz.insert_chart('A' + str(row + 2), chart)

            workbook.close()
            output.seek(0)

            response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=' + OCSA_name + '.xlsx'

        #now add in code to process this survey ID
            return response

        # response = HttpResponse(zipdata.read(), content_type='application/x-zip')
        # response['Content-Disposition'] = 'attachment; filename=DataZip.zip'

        #return response

def photosDownload(request, survey_id, login_name, survey_title, submission_id): 
    
    if login_name == "adamb":
           FHLogin = "adamb"
           FHPass = "cleanwaterpass"
           FHServer = "http://54.86.146.199"
           headers = {'Authorization':'Token 16d24bfe6de3e4c2c35dd68f8dc4d45cb62c16f4'}
    
    
    #JSON requests from FormHub API
    urlAnswers = FHServer + "/api/v1/data/" + FHLogin + '/' + survey_id
    urlQuestions = FHServer + "/api/v1/forms/" + FHLogin + '/' + survey_id + '/' + 'form.json'

    result = requests.get(urlAnswers, headers=headers)
    dataAnswers = json.loads(result.content)
    result = requests.get(urlQuestions, headers=headers)
    dataQuestions = json.loads(result.content)

    #fill Question dict with questions
    #communication_question_1, {question:“question”, answer:“answer”}
    questionDict = {}

    #Photo is 11th entry here, only photo and personalization are important
    for x in range (2, 12):
        for data in dataQuestions['children'][x]['children']:
            answerDict = {}
            answerDict['question'] = data['label']
            questionDict[data['name']] = answerDict

    #get response correlating to id of form 
    for responseNum in range(0, len(dataAnswers)):
        if (str(dataAnswers[responseNum]['_id']) == str(submission_id)):
  
            resultsDict = dataAnswers[responseNum]

            tempResultsDict = {}

            #trim the keys with "/"
            for key,value in resultsDict.iteritems():
                if "/" in key:
                    tempResultsDict[key.split("/")[1]] = resultsDict[key]

            resultsDict = tempResultsDict

            #combine questionDict and resultsDict
            for key,value in questionDict.iteritems():
                result = resultsDict.get(key)
                if (result):
                    #update answerDict in questionDict w/ results
                    answerDict = questionDict[key]
                    answerDict['answer'] = result
                    questionDict[key] = answerDict
                else:
                    answerDict = questionDict[key]
                    answerDict['answer'] = 'n/a'
                    questionDict[key] = answerDict

            #determine the number of questions in photo group and personalization group
            photoGroupSize = 0
            personalizationGroupSize = 0

            for key,value in questionDict.iteritems():
                if 'photo_question_' in key:
                    photoGroupSize += 1
                if 'personalization_question_' in key:
                    personalizationGroupSize += 1

            #setup zip file
            unzippedImages = BytesIO()
            zipdata = BytesIO()
            zipf = zipfile.ZipFile(zipdata, mode='w')

            #setup XLS file and write to buffer
            OCSA_name = questionDict.get('personalization_question_3')['answer']         
            workbook = xlsxwriter.Workbook(unzippedImages)
            worksheetPhotos = workbook.add_worksheet('Foto')

            #define formats for XLS
            formatWhite = workbook.add_format({'border': True, 'text_wrap' : True})
            formatPersonalization = workbook.add_format({'bg_color':'#FF0000', 'border': True, 'bold' : True})
            formatPhotos = workbook.add_format({'bg_color':'#92D050', 'border': True, 'bold' : True})

            #set column sizes for XLS format
            worksheetPhotos.set_column(0, 0, 10)
            worksheetPhotos.set_column(1, 1, 50)
            worksheetPhotos.set_column(2, 2, 30)
            worksheetPhotos.set_column(3, 3, 20)

            #write out Personalization section 
            row = 0
            col = 0

            #Personalization Header
            worksheetPhotos.write(row, col, '#', formatPersonalization)
            worksheetPhotos.write(row, col + 1, u'PERSONALIZACIÓN', formatPersonalization)
            worksheetPhotos.write(row, col + 2, 'REPUESTAS', formatPersonalization)

            row +=1

            #Personalization data
            for x in range (1, personalizationGroupSize):
                outputQuestion = questionDict.get('personalization_question_' + str(x))

                if(outputQuestion):
                    worksheetPhotos.write(row, col, outputQuestion.get('question').split(' ')[0], formatWhite)
                    worksheetPhotos.write(row, col + 1, outputQuestion.get('question'), formatWhite)
                    worksheetPhotos.write(row, col + 2, outputQuestion.get('answer'), formatWhite)
                    row += 1

            row += 2

            #Photo Header
            worksheetPhotos.write(row, col, '#', formatPhotos)
            worksheetPhotos.write(row, col + 1, u'FOTOS', formatPhotos)
            worksheetPhotos.write(row, col + 2, 'OBSERVACIONES / COMENTARIOS', formatPhotos)

            row += 1

            #Photo Data
            for x in range (1, photoGroupSize+1):
                outputQuestion = questionDict.get('photo_question_' + str(x))
                outputComment = questionDict.get('photo_comment_' + str(x))

                if(outputQuestion):
                    worksheetPhotos.write(row, col, outputQuestion.get('question').split(' ')[0], formatWhite)
                    worksheetPhotos.write(row, col + 1, outputQuestion.get('question'), formatWhite)
                if(outputComment):
                    worksheetPhotos.write(row, col + 2, outputComment.get('answer'), formatWhite)

                row += 1

            #Close workbook and write to zip file
            workbook.close()
            zipf.writestr(OCSA_name + ' Foto.xlsx', unzippedImages.getvalue())

            #Get photo attachement file names and retrieve them via URL, then add to byte stream
            for x in range (1, photoGroupSize+1):
                imageData = questionDict.get('photo_question_' + str(x))  
                if(imageData and imageData['answer'] != 'n/a'):        
                    url = 'http://54.86.146.199/attachment/original?media_file=' + FHLogin + '/attachments/' + imageData['answer']
                    unzippedImages = BytesIO(urlopen(url).read())
                    unzippedImages.seek(0)
                    zipf.writestr(imageData['question'] + '.jpg', unzippedImages.getvalue())


            zipf.close()
            zipdata.seek(0)

            #Write out zip to disk, need to change this to serve via http via Django
            # with open(OCSA_name + '.zip', 'w') as f:
            #     f.write(zipdata.getvalue())

            response = HttpResponse(zipdata.read(), content_type='application/x-zip')
            response['Content-Disposition'] = 'attachment; filename='+ OCSA_name + ' Photos.zip'

            return response