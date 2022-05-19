import re
from bs4 import BeautifulSoup


class UnstructuredHtmlToStructuredHtml:
    def __init__(self, file_name):
        self.html_file = file_name
        file_name = open(html_file)
        self.soup = BeautifulSoup(file_name, 'html.parser')

    def get_class_name(self):
        self.dictionary_to_store_class_name = {'h1': r'^Title\s\d+','Compiler’s Notes.':'Compiler’s Notes\.',   \
                                                'History_of_Section': 'History of Section\.','li_of_notes_to_decision':'Posting Requirement\.',\
                                               'li':r'^Chapter\s\d+','h3': r'^\d-\d-\d+','h2': r'^Chapter\s\d+','junk':'Text','ol':'\([a-z 0-9]\)'}
        for key in self.dictionary_to_store_class_name:
            tag_class = self.soup.find(lambda tag: tag.name == 'p' and re.search(self.dictionary_to_store_class_name[key], tag.text)  \
                         and (key == "ol" or key=="li_of_notes_to_decision" or tag.attrs['class'][0] not in self.dictionary_to_store_class_name.values()))
            if tag_class :
                class_name = tag_class['class'][0]
            self.dictionary_to_store_class_name[key] = class_name

    def convert_to_header_and_assign_id(self):
        list_to_store_regex = ['Compiler’s Notes\.','Compiler\'s Notes\.', 'Cross References\.', 'Comparative Legislation\.',
                               'Collateral References\.', 'NOTES TO DECISIONS', \
                               'Repealed Sections\.', 'Effective Dates\.', 'Law Reviews\.', 'Rules of Court\.']
        for tag in self.soup.find_all("p"):
            class_name=tag['class'][0]
            if class_name== self.dictionary_to_store_class_name['h1']:
                tag.name = "h1"
                title_number = re.search("^Title\s(?P<title_number>\d+)", tag.text).group('title_number')
                tag.attrs['id'] = 't' + title_number.zfill(2)
            elif class_name == self.dictionary_to_store_class_name['h2']:
                tag.name = "h2"
                chapter_number = re.search("^Chapter\s(?P<chapter_number>\d+)", tag.text).group('chapter_number')
                tag.attrs['id'] = tag.find_previous_sibling("h1").attrs['id'] + 'c' + chapter_number.zfill(2)
            elif class_name == self.dictionary_to_store_class_name['h3']:
                tag.name = "h3"
                tag.attrs['id'] = tag.find_previous_sibling("h2").attrs['id'] + 's' + re.search("^\d-\d-\d+(\.\d+)?", tag.text).group()

            elif class_name == self.dictionary_to_store_class_name['Compiler’s Notes.']:
                for expression in list_to_store_regex:
                    if re.search(expression,tag.text):
                        tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', tag.text).lower()
                        tag.attrs['id'] = tag.find_previous_sibling("h3").attrs['id'] + '-' + sub_section_id
                        if expression=='NOTES TO DECISIONS':
                            h5_tag = tag.find_next_sibling()
                            h5_tag.name = "h5"
                            for sub_tag in tag.find_next_siblings():
                                if sub_tag.next_element.name=="br" :
                                      continue
                                elif re.search('^\d-\d-\d+',sub_tag.text) or re.search('Collateral References\.',sub_tag.text):
                                    break
                                elif sub_tag.attrs['class'][0]==self.dictionary_to_store_class_name['li_of_notes_to_decision']:
                                    sub_tag.name="li"
                                    for sub_section_tag in sub_tag.find_next_siblings():
                                        if sub_section_tag.next_element.name=="br":
                                            continue
                                        elif sub_section_tag.name=="h3":
                                            break
                                        elif sub_section_tag.attrs['class'][0]==self.dictionary_to_store_class_name['Compiler’s Notes.'] and sub_section_tag.b :
                                            sub_section_tag.name="h5"
                                            sub_section_tag.attrs['id']=tag.attrs['id']+'-'+re.sub(r'[^a-zA-Z0-9]', '', sub_section_tag.text).lower()
            elif class_name == self.dictionary_to_store_class_name['History_of_Section']:
                if tag.b :
                    pattern = re.search("^History of Section\.", tag.text)
                    if pattern  :
                        text_from_b = tag.b.text
                        tag.b.decompose()
                        h4_tag = self.soup.new_tag("h4")
                        h4_tag.string = text_from_b
                        tag.insert_before(h4_tag)
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', h4_tag.text).lower()
                        h4_tag.attrs['id'] = h4_tag.find_previous_sibling("h3").attrs['id'] + '-' + sub_section_id

    def create_ul_tag_and_remove_junk(self):
        for tag in self.soup.find_all("p"):
            class_name=tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['li']:
                if re.search("^Chapter\s\d+", tag.text)  or re.search("^\d-\d-\d+",tag.text):
                    tag.name = "li"
            elif class_name == self.dictionary_to_store_class_name['junk']:
                tag.decompose()
        ul_tag_for_chapter = self.soup.new_tag("ul")
        ul_tag_for_section = self.soup.new_tag("ul")
        ul_tag_for_header5 = self.soup.new_tag("ul")
        li_count_for_chapter=0
        li_count_for_section=0
        li_count_for_notes_to_decision=0
        for li_tag in self.soup.find_all("li"):
            if re.search("^Chapter\s\d+", li_tag.text) :
                li_tag_text = li_tag.text
                li_tag.clear()
                chapter_number= re.search("^Chapter\s(?P<chapter_number>\d+)", li_tag_text).group('chapter_number')
                h2_id = li_tag.find_previous_sibling("h1").attrs['id'] + 'c' + chapter_number.zfill(2)
                li_tag.append(self.soup.new_tag("a", href='#' + h2_id))
                li_tag.a.string = li_tag_text
                li_count_for_chapter+=1
                li_tag['id']=h2_id+'-'+'cnav'+str(li_count_for_chapter).zfill(2)
                li_tag.wrap(ul_tag_for_chapter)
            elif re.search("^\d-\d-\d+", li_tag.text) :
                li_tag_text = li_tag.text
                li_tag.clear()
                nav_tag_for_section_ul = self.soup.new_tag("nav")
                h3_id = li_tag.find_previous_sibling("h2").attrs['id'] + 's' + re.search("^\d-\d-\d+(\.\d+)?",li_tag_text).group()
                li_tag.append(self.soup.new_tag("a", href='#' + h3_id))
                li_tag.a.string = li_tag_text
                li_count_for_section+=1
                li_tag['id'] = h3_id + '-' + 'snav' + str(li_count_for_section).zfill(2)
                h3_tag = li_tag.find_next_sibling()
                if h3_tag.name == "h3":
                    li_tag.wrap(ul_tag_for_section)
                    ul_tag_for_section.wrap(nav_tag_for_section_ul)
                    ul_tag_for_section = self.soup.new_tag("ul")
                    nav_tag_for_section_ul = self.soup.new_tag("nav")
                    li_count_for_section = 0
                else:
                    li_tag.wrap(ul_tag_for_section)
            else:
                li_tag_text = li_tag.text
                li_tag.clear()
                nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', li_tag_text).lower()
                h5_id = li_tag.find_previous_sibling("h4").attrs['id'] + '-' + sub_section_id
                li_tag.append(self.soup.new_tag("a", href='#' + h5_id))
                li_tag.a.string = li_tag_text
                li_count_for_notes_to_decision+=1
                h4_id = li_tag.find_previous_sibling("h4").attrs['id']
                if li_tag.find_next_sibling().name == "h5":
                    li_tag.wrap(ul_tag_for_header5)
                    ul_tag_for_header5.wrap(nav_tag_for_notes_to_decision_ul)
                    ul_tag_for_header5 = self.soup.new_tag("ul")
                    nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                else:
                    li_tag.wrap(ul_tag_for_header5)

    def create_nav_and_main_tag(self):
        nav_tag_for_header_and_chapter = self.soup.new_tag("nav")
        main_tag = self.soup.new_tag("main")
        self.soup.find("h1").wrap(nav_tag_for_header_and_chapter)
        self.soup.find("ul").wrap(nav_tag_for_header_and_chapter)
        nav_tag=self.soup.find("nav")
        for tag in nav_tag.find_next_siblings():
            tag.wrap(main_tag)

    def create_ol_tag_and_assign_id(self):
        ol_alphabet_count=1
        ol_number_count=1
        ol_tag_for_roman=self.soup.new_tag("ol",type='i')
        ol_tag_for_number=self.soup.new_tag("ol",type)
        ol_tag_for_alphabet=self.soup.new_tag("ol",type='a')
        for tag in self.soup.main.find_all("p",class_=self.dictionary_to_store_class_name['ol']):
            if re.search('\([a-z 0-9]\)|\([0-2][0-9]\)|\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)',tag.text):
                next_tag = tag.find_next_sibling()
                if next_tag.next_element.name == 'br':
                    next_tag.decompose()
                    next_tag=tag.find_next_sibling()
                if next_tag.name!='h4':
                    if re.search('^\([a-z]\)\s\([0-9]\)',tag.text.strip()) :
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        ol_id_of_alphabet = re.search('^\((?P<ol_id_alphabet>[a-z])\)', tag.text.strip()).group('ol_id_alphabet')
                        ol_id_of_number = re.search('\((?P<ol_id_number>[0-9]|[0-2][0-9])\)', tag.text.strip()).group('ol_id_number')
                        text=tag.text.replace(re.search('\([a-z]\)\s\([0-9]\)',tag.text.strip()).group(),'')
                        tag.string=text
                        tag.wrap(ol_tag_for_number)
                        li_tag=self.soup.new_tag("li")
                        li_tag['id']=h3_id +'ol'+str(ol_alphabet_count)+ol_id_of_alphabet
                        li_tag.append(ol_tag_for_number)
                        tag.attrs['id'] = h3_id + 'ol' + str(ol_alphabet_count) + ol_id_of_alphabet+ol_id_of_number
                        ol_tag_for_alphabet.append(li_tag)
                    elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()) :
                        tag.name = "li"
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('roman_id')
                        text = tag.text.replace(re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_roman)
                        tag['id'] = ol_tag_for_number.find_all("li")[-1].attrs['id'] + roman_id
                        if re.search('^\([0-9]\)|^\([0-2][0-9]\)', next_tag.text.strip()) :
                            ol_tag_for_number.find_all("li")[-1].append(ol_tag_for_roman)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        elif re.search('^\([a-z]\)',next_tag.text.strip()) :
                            ol_tag_for_number.find_all("li")[-1].append(ol_tag_for_roman)
                            ol_tag_for_alphabet.find_all("li")[-1].append(ol_tag_for_number)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            ol_tag_for_number = self.soup.new_tag("ol")
                        else:
                            continue
                    elif re.search('^\([a-z]\)', tag.text.strip()) :
                        tag.name = "li"
                        h3_id=tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('^\((?P<ol_id>[a-z])\)', tag.text.strip()).group('ol_id')
                        text = tag.text.replace(re.search('^\([a-z]\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_alphabet)
                        tag.attrs['id'] = h3_id + 'ol' + str(ol_alphabet_count) +alphabet_id
                        if re.search('^[a-z A-Z]+',next_tag.text.strip()) is None:
                            continue
                        else:
                            second_next_tag=next_tag.find_next_sibling()
                            if re.search('^\([a-z]\)', second_next_tag.text.strip()) :
                                ol_tag_for_alphabet.append(next_tag)
                            else:
                                ol_tag_for_alphabet=self.soup.new_tag("ol",type="a")
                    elif re.search('^\([0-9]\)|^\([0-2][0-9]\)',tag.text.strip()) :
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        number_id = re.search('^\((?P<ol_id>[0-9]|[0-2][0-9])\)', tag.text.strip()).group('ol_id')
                        text = tag.text.replace(re.search('^\([0-9]\)|^\([0-2][0-9]\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_number)
                        if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)',next_tag.text.strip())  or re.search('^\([a-z]\)|^[a-z]+',next_tag.text.strip()) is None:
                            if ol_tag_for_alphabet.li :
                                tag['id'] = ol_tag_for_alphabet.find_all("li")[-1].attrs['id'] + number_id
                            else:
                                tag['id'] = h3_id+'ol'+str(ol_number_count)+number_id

                        else:
                            if ol_tag_for_alphabet.li :
                                tag['id']=ol_tag_for_alphabet.find_all("li")[-1].attrs['id']+number_id
                                ol_tag_for_alphabet.find_all("li")[-1].append(ol_tag_for_number)
                                ol_tag_for_number=self.soup.new_tag("ol")
                            else:
                                tag['id']=h3_id+'ol'+str(ol_number_count)+number_id
                                ol_tag_for_number=self.soup.new_tag("ol")
                else:
                    if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()) :
                        tag.name = "li"
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',tag.text.strip()).group('roman_id')
                        text = tag.text.replace(re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_roman)
                        tag['id']=ol_tag_for_number.find_all("li")[-1].attrs['id']+roman_id
                        ol_tag_for_number.find_all("li")[-1].append(ol_tag_for_roman)
                        ol_tag_for_number.wrap(ol_tag_for_alphabet)
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    elif re.search('^\([a-z]\)', tag.text.strip()) :
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('^\((?P<ol_id>[a-z])\)', tag.text.strip()).group('ol_id')
                        text = tag.text.replace(re.search('^\([a-z]\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_alphabet)
                        tag.attrs['id'] = h3_id + 'ol' + str(ol_alphabet_count) +alphabet_id
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    elif re.search('^\([0-9]\)|^\([0-2][0-9]\)',tag.text.strip()) :
                        tag.name = "li"
                        number_id = re.search('^\((?P<ol_id>[0-9]|[0-2][0-9])\)', tag.text.strip()).group('ol_id')
                        text = tag.text.replace(re.search('^\([0-9]\)|^\([0-2][0-9]\)', tag.text.strip()).group(), '')
                        tag.string = text
                        tag.wrap(ol_tag_for_number)
                        if ol_tag_for_alphabet.li :
                            tag['id']=ol_tag_for_alphabet.find_all("li")[-1].attrs['id']+number_id
                            ol_tag_for_alphabet.find_all("li")[-1].append(ol_tag_for_number)
                        else:
                            tag['id'] = h3_id + 'ol' + str(ol_number_count) + number_id
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_alphabet=self.soup.new_tag("ol",type="a")

    def create_div_tag(self):
        div_tag_for_chapter = self.soup.new_tag("div")
        div_tag_for_section = self.soup.new_tag("div")
        div_tag_for_h4 = self.soup.new_tag("div")
        div_tag_for_h5=self.soup.new_tag("div")
        for tag in self.soup.find_all("h2"):
            next_tag=tag.find_next_sibling()
            div_tag_for_chapter.append(tag)
            if next_tag.name=="nav":
                sibling_of_nav=next_tag.find_next_sibling()
                div_tag_for_chapter.append(next_tag)
                next_tag=sibling_of_nav
                if next_tag.name == "h3":
                    tag_of_h3 = next_tag.find_next_sibling()
                    next_tag.wrap(div_tag_for_section)
                    while tag_of_h3.name != "h3" and tag_of_h3.name!="h2" and tag_of_h3.name!="div":
                        if tag_of_h3.name == "h4":
                            tag_of_h4 = tag_of_h3.find_next_sibling()
                            tag_of_h3.wrap(div_tag_for_h4)
                            while tag_of_h4  and tag_of_h4.name != "h4" and tag_of_h4.name!="h2" and tag_of_h4.name!="div":
                                if tag_of_h4.name == "h3":
                                    if div_tag_for_h4.next_element :
                                        div_tag_for_section.append(div_tag_for_h4)
                                    if div_tag_for_section.next_element :
                                        div_tag_for_chapter.append(div_tag_for_section)
                                    div_tag_for_section = self.soup.new_tag("div")
                                    div_tag_for_h4 = self.soup.new_tag("div")
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                    if tag_of_h4.name=="p":
                                        next_tag=tag_of_h4.find_next_sibling()
                                        div_tag_for_section.append(tag_of_h4)
                                        tag_of_h4=next_tag
                                elif tag_of_h4.name=="h5":
                                    tag_of_h5=tag_of_h4.find_next_sibling()
                                    tag_of_h4.wrap(div_tag_for_h5)
                                    while tag_of_h5.name!="h5" and tag_of_h5.name!="h3":
                                        if tag_of_h5.next_element.name=="br":
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5=self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4=self.soup.new_tag("div")
                                            div_tag_for_section.append(tag_of_h5)
                                            tag_of_h5 = next_tag
                                        elif tag_of_h5.name=="h4":
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5 = self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                            break
                                        else:
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h5.append(tag_of_h5)
                                            tag_of_h5=next_tag
                                    if div_tag_for_h5.next_element:
                                        div_tag_for_h4.append(div_tag_for_h5)
                                    div_tag_for_h5=self.soup.new_tag("div")
                                    tag_of_h4=tag_of_h5

                                elif tag_of_h4.next_element.name == "br":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(div_tag_for_h4)
                                    div_tag_for_h4 = self.soup.new_tag("div")
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                    if tag_of_h4.name=="h2":
                                        div_tag_for_chapter.append(div_tag_for_section)
                                        self.soup.main.append(div_tag_for_chapter)
                                        div_tag_for_section=self.soup.new_tag("div")
                                        div_tag_for_chapter=self.soup.new_tag("div")
                                elif tag_of_h4.name == "nav":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_h4.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                elif tag_of_h4.name == "ol":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag

                                else:
                                    next_tag = tag_of_h4.find_next_sibling()
                                    if div_tag_for_h4.next_element:
                                        div_tag_for_h4.append(tag_of_h4)
                                    else:
                                        div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                            if div_tag_for_h4.next_element :
                                div_tag_for_section.append(div_tag_for_h4)
                                div_tag_for_h4=self.soup.new_tag("div")
                        else:
                            next_tag = tag_of_h3.find_next_sibling()
                            div_tag_for_section.append(tag_of_h3)

                        tag_of_h3 = next_tag
                    if tag_of_h3.name=="div":
                        div_tag_for_chapter.append(div_tag_for_section)
                        self.soup.main.append(div_tag_for_chapter)
                    self.write_to_file()

    def write_to_file(self):
        file_write = open("/home/mis/Downloads/modified.html", "w")
        file_write.write(self.soup.prettify())

html_file = "/home/mis/Downloads/raw.html"
unstructured_to_structured_html = UnstructuredHtmlToStructuredHtml(html_file)
unstructured_to_structured_html.get_class_name()
unstructured_to_structured_html.convert_to_header_and_assign_id()
unstructured_to_structured_html.create_ul_tag_and_remove_junk()
unstructured_to_structured_html.create_nav_and_main_tag()
unstructured_to_structured_html.create_ol_tag_and_assign_id()
unstructured_to_structured_html.create_div_tag()
unstructured_to_structured_html.write_to_file()
