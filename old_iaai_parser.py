from requests_html import HTMLSession
session = HTMLSession()
r = session.get('https://www.iaai.com/Search?crefiners=|yearfilter:2017-2019&keyword=GTI')
about = r.html.find('#dvSearchList .table tbody tr')
for i in about:
    line = i.text.split('\n')
    mi = 0
    try:
      mi = int(line[4].replace('k mi', ''))
      mi = round(mi*1.6)
    except ValueError:
      pass
    print('{0} ID:{1} - {2}k km [{3}]'.format(line[0].split(' ')[0], line[2], mi, line[5]))
