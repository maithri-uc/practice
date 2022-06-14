import re
from roman import*
from bs4 import BeautifulSoup


class UnstructuredHtmlToStructuredHtml:
    def __init__(self, file_name):
        self.html_file = file_name
        file_name = open(html_file)
        self.soup = BeautifulSoup(file_name, 'html.parser')

    def get_class_name(self):
        self.dictionary_to_store_class_name = {'h1': r'^Title \d+', 'h4': 'Compiler’s Notes\.',
                                               'History': 'History of Section\.',
                                               'li': r'^Chapters? \d+(.\d+)?',
                                               'h3': r'^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?',
                                               'h2': r'^Chapters? \d+(.\d+)?',
                                               'junk': 'Text','ol_of_i':'\([A-Z]\)'}
        for key in self.dictionary_to_store_class_name:
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.dictionary_to_store_class_name[key], tag.text.strip())
                            and  tag.attrs['class'][0] not in
                                 self.dictionary_to_store_class_name.values())
            if tag_class:
                class_name = tag_class['class'][0]
                self.dictionary_to_store_class_name[key] = class_name
        print(self.dictionary_to_store_class_name)

    def remove_junk(self):
        for tag in self.soup.find_all("p"):
            class_name = tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['junk']:
                if re.search('Annotations|Text|History',tag.text):
                    tag.decompose()

    def convert_to_header_and_assign_id(self):
        list_to_store_regex_for_h4 = ['Compiler’s Notes.', 'Compiler\'s Notes.', 'Cross References.',
                                      'Comparative Legislation.',
                                      'Collateral References.', 'NOTES TO DECISIONS',
                                      'Repealed Sections.', 'Effective Dates.', 'Law Reviews.', 'Rules of Court.']
        count_for_duplicate = 0
        for tag in self.soup.find_all("p"):

            class_name = tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['h1']:
                tag.name = "h1"
                if re.search("^Title (?P<title_number>\d+)", tag.text):
                    title_number = re.search("^Title (?P<title_number>\d+)", tag.text).group('title_number').zfill(2)
                    tag.attrs['id'] = f"t{title_number}"
                else:
                    raise Exception('Title Not found...')
            elif class_name == self.dictionary_to_store_class_name['h2']:
                tag.name = "h2"
                if re.search("^Chapters? \d+(.\d+)?", tag.text):
                    h1_id=tag.find_previous_sibling("h1").attrs['id']
                    chapter_number = re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?)", tag.text).group('chapter_number').zfill(2)
                    tag.attrs['id'] = f"{h1_id}c{chapter_number}"
                    tag.attrs['class']="chapter"
                elif re.search("^Part \d{1,2}", tag.text):
                    part_number = re.search("^Part (?P<part_number>\d{1,2})", tag.text).group('part_number').zfill(2)
                    h2_id=tag.find_previous_sibling("h2",class_='chapter').attrs['id']
                    tag.attrs['id'] = f"{h2_id}p{part_number}"
                else:
                    raise Exception('header2 pattern Not found...')
            elif class_name == self.dictionary_to_store_class_name['h3']:
                tag.name = "h3"
                tag['class'] = "section"
                h2_id=tag.find_previous_sibling("h2").attrs['id']
                if re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", tag.text.strip()):
                    section_id=re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", tag.text.strip()).group()
                    section_id=f"{h2_id}s{section_id}"
                    duplicate = self.soup.find_all("h3", id=section_id)
                    if len(duplicate):#4-1.1-1
                        count_for_duplicate+=1
                        id_count=str(count_for_duplicate).zfill(2)
                        tag.attrs['id'] = f"{section_id}.{id_count}"
                    else:
                        count_for_duplicate=0
                        tag.attrs['id'] = section_id
                else:
                    print(tag)
                    raise Exception('section pattern not found...')

            elif class_name == self.dictionary_to_store_class_name['h4']:
                if tag.text.strip() in list_to_store_regex_for_h4:
                    tag.name="h4"
                    h2_id=tag.find_previous_sibling("h2").attrs['id']
                    h3_id=tag.find_previous_sibling("h3").attrs['id']
                    sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', tag.text).lower()
                    if tag.find_previous_sibling().attrs['class'][0] == self.dictionary_to_store_class_name['li']:  # t3c13repealed section
                        tag.attrs['id'] = f"{h2_id}-{sub_section_id}"
                    else:
                        tag.attrs['id'] = f"{h3_id}-{sub_section_id}"
                if tag.text.strip()=='NOTES TO DECISIONS':
                    tag_id=tag.attrs['id']
                    for sub_tag in tag.find_next_siblings():
                        class_name=sub_tag.attrs['class'][0]
                        if class_name==self.dictionary_to_store_class_name['History']:
                            sub_tag.name='li'
                        elif class_name == self.dictionary_to_store_class_name['h4'] and sub_tag.b and re.search('Collateral References\.',sub_tag.text) is None :
                            sub_tag.name = "h5"
                            sub_tag_id=re.sub(r'[^a-zA-Z0-9]', '', sub_tag.text).lower()
                            if re.search('^—.*', sub_tag.text):
                                previous_tag_id = sub_tag.find_previous_sibling("h5",class_="notes_section").attrs['id']
                                sub_tag.attrs['id'] = f"{previous_tag_id}-{sub_tag_id}"
                            else:
                                sub_tag.attrs['id'] = f"{tag_id}-{sub_tag_id}"
                                sub_tag.attrs['class']='notes_section'
                        elif re.search('^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?',sub_tag.text) or re.search('Collateral References\.',sub_tag.text) or re.search('^Part \d{1,2}', sub_tag.text) or re.search('^Chapters? \d+(.\d+)?', sub_tag.text):
                            break
            elif class_name == self.dictionary_to_store_class_name['History']:
                if re.search("^History of Section\.", tag.text):
                    h4_tag = self.soup.new_tag("h4")
                    h4_tag.string = "History of Section."
                    tag.insert_before(h4_tag)
                    tag.string = re.sub('History of Section.', '', tag.text)
                    sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', h4_tag.text).lower()
                    h3_id = h4_tag.find_previous_sibling("h3").attrs['id']
                    h2_id=h4_tag.find_previous_sibling("h2").attrs['id']
                    if h4_tag.find_previous_sibling().attrs['class'][0] == self.dictionary_to_store_class_name['li']:  # history of section
                        h4_tag.attrs['id'] = f"{h2_id}-{sub_section_id}"
                    else:
                        h4_tag.attrs['id'] = f"{h3_id}-{sub_section_id}"
                elif re.search("^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})",tag.text.strip(),re.IGNORECASE):
                    tag.name="h3"
                    h3_id=tag.find_previous_sibling("h3",class_="section").attrs['id']
                    article_id=re.search("^ARTICLE (?P<article_id>(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))",tag.text.strip(),re.IGNORECASE).group('article_id')
                    tag['id']=f"{h3_id}a{article_id}"
                elif re.search("^Section \d+. [a-z ,\-A-Z]+\. \(a\)",tag.text.strip()):#section 14
                    text_from_b=tag.text.split('(a)')
                    p_tag_for_section=self.soup.new_tag("p")
                    p_tag_for_section.string=text_from_b[0]
                    p_tag_for_a=self.soup.new_tag("p")
                    p_tag_text=f"(a){text_from_b[1]}"
                    p_tag_for_a.string=p_tag_text
                    tag.insert_before(p_tag_for_section)
                    tag.insert_before(p_tag_for_a)
                    p_tag_for_a.attrs['class'] = [self.dictionary_to_store_class_name['History']]
                    p_tag_for_section.attrs['class'] = [self.dictionary_to_store_class_name['History']]
                    tag.decompose()
            elif class_name == self.dictionary_to_store_class_name['li']:
                if re.search("^Chapters? \d+(.\d+)?", tag.text.strip()) or re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?",tag.text.strip()) or re.search('^Part \d{1,2}',tag.text.strip()):
                    tag.name = "li"
                    tag['class']="nav_li"

    def create_nav_and_ul_tag(self):
        ul_tag_for_chapter = self.soup.new_tag("ul")
        ul_tag_for_section = self.soup.new_tag("ul")
        ul_tag_for_header5 = self.soup.new_tag("ul")
        ul_tag_for_sub_section = self.soup.new_tag("ul")
        ul_tag_for_part=self.soup.new_tag("ul")
        li_count_for_chapter = 0
        li_count_for_section = 0
        li_count_for_part=0
        count_for_duplicate = 0
        for li_tag in self.soup.find_all("li"):
            if re.search("^Chapters? \d+(.\d+)?", li_tag.text.strip()):
                li_tag_text = li_tag.text
                li_tag.clear()
                if re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?)", li_tag_text):
                    chapter_number = re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?)", li_tag_text).group('chapter_number').zfill(2)
                    h1_id=li_tag.find_previous_sibling("h1").attrs['id']
                    h2_id = f"{h1_id}c{chapter_number}"
                else:
                    raise Exception('chapter li pattern not found')
                li_tag.append(self.soup.new_tag("a", href='#' + h2_id))
                li_tag.a.string = li_tag_text
                li_count_for_chapter += 1
                li_count=str(li_count_for_chapter).zfill(2)
                li_tag['id'] = f"{h2_id}-cnav{li_count}"
                ul_tag_for_chapter.attrs['class'] = 'leaders'
                li_tag.wrap(ul_tag_for_chapter)
            elif re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag.text.strip()):
                li_tag_text = li_tag.text
                li_tag.clear()
                nav_tag_for_section_ul = self.soup.new_tag("nav")
                if re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag_text):
                    h2_id=li_tag.find_previous_sibling("h2").attrs['id']
                    section_id=re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag_text).group()
                    h3_id = f"{h2_id}s{section_id}"
                    duplicate = self.soup.find_all("a", href='#' + h3_id)
                    if len(duplicate):
                        count_for_duplicate += 1
                        id_count = str(count_for_duplicate).zfill(2)
                        h3_id = f"{h3_id}.{id_count}"
                    else:
                        count_for_duplicate = 0
                else:
                    raise Exception('section li pattern not found')
                li_tag.append(self.soup.new_tag("a", href='#' + h3_id))
                li_tag.a.string = li_tag_text
                li_count_for_section += 1
                li_count=str(li_count_for_section).zfill(2)
                li_tag['id'] = f"{h3_id}-snav{li_count}"
                h3_tag = li_tag.find_next_sibling()
                ul_tag_for_section.attrs['class'] = 'leaders'
                if h3_tag.name == "h3" or h3_tag.name == "h4":
                    li_tag.wrap(ul_tag_for_section)
                    ul_tag_for_section.wrap(nav_tag_for_section_ul)
                    ul_tag_for_section = self.soup.new_tag("ul")
                    nav_tag_for_section_ul = self.soup.new_tag("nav")
                    li_count_for_section = 0
                else:
                    li_tag.wrap(ul_tag_for_section)
            elif re.search("^Part \d{1,2}", li_tag.text.strip()):
                li_tag_text = li_tag.text
                li_tag.clear()
                nav_tag_for_part_ul = self.soup.new_tag("nav")
                if re.search("^Part \d{1,2}", li_tag_text):
                    h2_id = li_tag.find_previous_sibling("h2").attrs['id']
                    part_id = re.search("^Part (?P<part_number>\d{1,2})", li_tag_text).group('part_number').zfill(2)
                    part_section_id = f"{h2_id}p{part_id}"
                else:
                    raise Exception('part li pattern not found')
                li_tag.append(self.soup.new_tag("a", href='#' + part_section_id))
                li_tag.a.string = li_tag_text
                li_count_for_part += 1
                li_count = str(li_count_for_part).zfill(2)
                li_tag['id'] = f"{h2_id}-snav{li_count}"
                h3_tag = li_tag.find_next_sibling()
                ul_tag_for_part.attrs['class'] = 'leaders'
                if h3_tag.name == "h2" :
                    li_tag.wrap(ul_tag_for_part)
                    ul_tag_for_part.wrap(nav_tag_for_part_ul)
                    ul_tag_for_part= self.soup.new_tag("ul")
                    nav_tag_for_part_ul = self.soup.new_tag("nav")
                    li_count_for_part = 0
                else:
                    li_tag.wrap(ul_tag_for_part)
            else:
                ul_tag_for_sub_section.attrs['class'] = 'leaders'
                ul_tag_for_header5.attrs['class'] = 'leaders'
                if re.search('^—.*', li_tag.text.strip()):
                    li_tag_text = li_tag.text
                    li_tag.clear()
                    id_of_inner_li = re.sub(r'[^a-zA-Z0-9]', '', li_tag_text).lower()
                    previous_tag = li_tag.find_previous_sibling()
                    if re.search('^—.*', previous_tag.find_all("li")[-1].text.strip()):
                        id_of_parent = re.sub(r'[^a-zA-Z0-9]', '', previous_tag.find_previous_sibling().find_all("li")[-1].text).lower()
                    else:
                        id_of_parent = re.sub(r'[^a-zA-Z0-9]', '', previous_tag.find_all("li")[-1].text).lower()
                    h4_id=li_tag.find_previous_sibling("h4").attrs['id']
                    h5_id = f"{h4_id}-{id_of_parent}-{id_of_inner_li}"
                    li_tag.append(self.soup.new_tag("a", href='#' + h5_id))
                    li_tag.a.string = li_tag_text
                    if re.search('^—.*', li_tag.find_next_sibling().text.strip()):
                        li_tag.wrap(ul_tag_for_sub_section)
                    elif li_tag.find_next_sibling().name == "h5":
                        li_tag.wrap(ul_tag_for_sub_section)
                        ul_tag_for_header5.find_all("li")[-1].append(ul_tag_for_sub_section)
                        ul_tag_for_sub_section = self.soup.new_tag("ul")
                        ul_tag_for_header5.wrap(nav_tag_for_notes_to_decision_ul)
                        ul_tag_for_header5 = self.soup.new_tag("ul")
                    else:
                        li_tag.wrap(ul_tag_for_sub_section)
                        ul_tag_for_header5.find_all("li")[-1].append(ul_tag_for_sub_section)
                        ul_tag_for_sub_section = self.soup.new_tag("ul")
                else:
                    li_tag_text = li_tag.text
                    li_tag.clear()
                    sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', li_tag_text).lower()
                    h4_id=li_tag.find_previous_sibling("h4").attrs['id']
                    h5_id = f"{h4_id}-{sub_section_id}"
                    li_tag.append(self.soup.new_tag("a", href='#' + h5_id))
                    li_tag.a.string = li_tag_text
                    nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                    if li_tag.find_next_sibling().name == "h5":
                        li_tag.wrap(ul_tag_for_header5)
                        ul_tag_for_header5.wrap(nav_tag_for_notes_to_decision_ul)
                        ul_tag_for_header5 = self.soup.new_tag("ul")
                        nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                    else:
                        li_tag.wrap(ul_tag_for_header5)

    def create_nav_and_main_tag(self):
        nav_tag_for_header1_and_chapter = self.soup.new_tag("nav")
        main_tag = self.soup.new_tag("main")
        self.soup.find("h1").wrap(nav_tag_for_header1_and_chapter)
        self.soup.find("ul").wrap(nav_tag_for_header1_and_chapter)
        for tag in nav_tag_for_header1_and_chapter.find_next_siblings():
            tag.wrap(main_tag)

    def add_citation(self):
        for tag in self.soup.find_all(["p", "li"]):
            tag_string = ''
            if re.search('Defendant could be held liable for operating a motor vehicle',tag.text):
                print()
            if re.search('(\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?)', tag.text.strip()) and tag.attrs['class']!="nav_li":
                for pattern in sorted(set(match[0] for match in re.findall('(\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?)', tag.text.strip()))):
                    if re.search('\d+-\d+-\d+\.\d+',pattern):
                        section_match = re.search("(?P<title_id>\d+)-(?P<chapter_id>\d+)(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?",pattern)
                        tag_id=f"t{section_match.group('title_id').zfill(2)}c{section_match.group('chapter_id').zfill(2)}s{section_match.group()}"
                        text = tag.text
                        if self.soup.find("h3",id=id):
                            tag_string = re.sub(pattern,f"<cite><a href=#{tag_id}>{pattern}</a></cite>", text)
                        else:
                            tag_string=re.sub(pattern,f"<cite><a href=#http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=6n086vb5r88s4tlhtc0rub0d9r&_ij_reload=RELOAD_ON_SAVE#{tag_id}>{pattern}</a></cite>", text)
                        tag.clear()
                        tag.string = tag_string
                    else:
                        section_match = re.search("(?P<title_id>\d+)-(?P<chapter_id>\d+)(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?",pattern)
                        tag_id = f"t{section_match.group('title_id').zfill(2)}c{section_match.group('chapter_id').zfill(2)}s{section_match.group()}"
                        text = tag.text
                        if self.soup.find(id=tag_id):
                            tag_string = re.sub(pattern+'(?!((\d)?.\d+))', f"<cite><a href=#{tag_id}>{pattern}</a></cite>", text)
                        else:
                            tag_string = re.sub(pattern+'(?!((\d)?.\d+))',f"<cite><a href=#http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=6n086vb5r88s4tlhtc0rub0d9r&_ij_reload=RELOAD_ON_SAVE#{tag_id}>{pattern}</a></cite>",text)
                        tag.clear()
                        tag.string = tag_string

            if re.search('\d+ A.(L.R.)?( Fed. )?(\d[a-z]{1,2})?( Art.)? ?\d+', tag.text.strip())  and tag.attrs['class']!="nav_li":
                for alr_pattern in set(match[0] for match in re.findall('(\d+ A.(L.R.)?( Fed. )?(\d[a-z]{1,2})?( Art.)? ?\d+)', tag.text.strip())):
                    if re.search(alr_pattern, tag.text):
                        cite_tag = self.soup.new_tag("cite")
                        text_string = re.search(alr_pattern, tag.text).group()
                        cite_tag.string = text_string
                        text = tag.text
                        tag_string = re.sub(text_string, f"<cite>{alr_pattern}</cite>", text)
                        tag.clear()
                        tag.string = tag_string

            if re.search('[PG]\.L\. \d+', tag.text.strip()) and tag.attrs['class']!="nav_li":
                for pl_pattern in set(match for match in re.findall('([PG]\.L\. \d+)', tag.text.strip())):
                    text_string = re.search(pl_pattern, tag.text).group()
                    text = tag.text
                    tag_string = re.sub(text_string, f"<cite>{pl_pattern}</cite>", text)
                    tag.clear()
                    tag.string = tag_string

            if re.search('\d+ R\.I\. (LEXIS )?\d+',tag.text.strip())and tag.attrs['class']!="nav_li":
                for rl_pattern in set(match[0] for match in re.findall('(\d+ R\.I\. (LEXIS )?\d+)', tag.text.strip())):
                    text_string = re.search(rl_pattern, tag.text).group()
                    text = tag.text
                    tag_string = re.sub(text_string, f"<cite>{rl_pattern}</cite>", text)
                    tag.clear()
                    tag.string = tag_string

            if re.search('\d+ A\.2d \d+',tag.text.strip())and tag.attrs['class']!="nav_li":
                for a2d_pattern in set(match for match in re.findall('\d+ A\.2d \d+', tag.text.strip())):
                    text_string = re.search(a2d_pattern, tag.text).group()
                    text = tag.text
                    tag_string = re.sub(text_string, f"<cite>{a2d_pattern}</cite>", text)
                    tag.clear()
                    tag.string = tag_string

            if tag_string:
                tag.clear()
                tag.append(BeautifulSoup(tag_string, features="html.parser"))

    def create_ol_tag(self):
        alphabet='a'
        number=1
        roman='i'
        inner_roman='i'
        caps_alpha='A'
        inner_num=1
        caps_roman='I'
        inner_alphabet='a'
        ol_count = 1
        ol_inner_number_count=1
        ol_tag_for_roman = self.soup.new_tag("ol", type='i')
        ol_tag_for_number = self.soup.new_tag("ol")
        ol_tag_for_alphabet = self.soup.new_tag("ol", type='a')
        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
        ol_tag_for_inner_number=self.soup.new_tag("ol")
        ol_tag_for_inner_roman=self.soup.new_tag("ol",type="i")
        ol_tag_for_inner_alphabet=self.soup.new_tag("ol",type="a")
        for tag in self.soup.main.find_all("p"):
            if tag.name==None:
                continue
            if tag['class'][0]==self.dictionary_to_store_class_name['History'] or tag['class'][0]==self.dictionary_to_store_class_name['ol_of_i']:
                if re.search("^[a-z A-Z]+", tag.text) :
                    next_sibling=tag.find_next_sibling()
                    if next_sibling and re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',next_sibling.text.strip()):
                        ol_count=1
                    continue
                next_tag = tag.find_next_sibling()
                if next_tag is None:#last tag
                    break
                if next_tag.next_element.name and next_tag.next_element.name == 'br':
                    next_tag.decompose()
                    next_tag = tag.find_next_sibling()
                if next_tag.name != 'h4':
                    if re.search('^\(\d{1,2}\) \((ix|iv|v?i{0,3})\) \([A-Z]\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        ol_id_of_roman = re.search('\((?P<ol_id_roman>(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('ol_id_roman')
                        alphabet_id = re.search('\((?P<alphabet_id>[A-Z])\)', tag.text.strip()).group('alphabet_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\(\d{1,2}\) \((ix|iv|v?i{0,3})\) \([A-Z]\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha=chr(ord(caps_alpha)+1)
                        li_tag_for_number = self.soup.new_tag("li")
                        li_tag_for_number['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag_for_roman = self.soup.new_tag("li")
                        li_tag_for_roman['id'] = f"{h3_id}ol{ol_count}{ol_id_of_roman}"
                        li_tag_for_number['class'] = "number"
                        li_tag.append(ol_tag_for_roman)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_roman}"
                        li_tag_for_roman['class']="roman"
                        li_tag_for_roman.append(ol_tag_for_caps_alphabet)
                        ol_tag_for_roman.append(li_tag_for_roman)
                        li_tag_for_number.append(ol_tag_for_roman)
                        ol_tag_for_number.append(li_tag_for_number)
                        number += 1
                        roman = fromRoman(ol_id_of_roman.upper())
                        roman += 1
                        roman = toRoman(roman).lower()
                    elif re.search('^\([a-z]\) \(\d\)', tag.text.strip()):
                        count_of_p_tag=0
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        ol_id_of_alphabet = re.search('^\((?P<ol_id_alphabet>[a-z])\)', tag.text.strip()).group('ol_id_alphabet')
                        ol_id_of_number = re.search('\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        list_store_text=[]
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text=''.join(list_store_text)
                        text = text.replace(re.search('\([a-z]\) \(\d\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_number)
                        number+=1
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_alphabet}"
                        li_tag['class']="alphabet"
                        ol_tag_for_number.wrap(li_tag)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_alphabet}{ol_id_of_number}"
                        tag['class']="number"
                        li_tag.wrap(ol_tag_for_alphabet)
                        alphabet=chr(ord(alphabet)+1)
                        if re.search('^[a-z A-Z]+', next_tag.text.strip()):
                            while re.search("^[a-z A-Z]+", next_tag.text.strip()):
                                sub_tag = next_tag.find_next_sibling()
                                p_tag=self.soup.new_tag("p")
                                p_tag.string=next_tag.text
                                p_tag['id'] = f"{tag['id']}.{count_of_p_tag}"
                                p_tag['class']=next_tag['class']
                                tag.append(p_tag)
                                next_tag.decompose()
                                next_tag = sub_tag
                    elif re.search('^\(\d{1,2}\) \((ix|iv|v?i{0,3})\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        ol_id_of_roman = re.search('\((?P<ol_id_roman>(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('ol_id_roman')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\(\d{1,2}\) \((ix|iv|v?i{0,3})\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_roman)
                        roman=fromRoman(ol_id_of_roman.upper())
                        roman+=1
                        roman=toRoman(roman).lower()
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag['class']="number"
                        li_tag.append(ol_tag_for_roman)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_roman}"
                        tag['class']="roman"
                        ol_tag_for_number.append(li_tag)
                        number+=1
                    elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\) \([A-Z]\)',tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('\((?P<alphabet_id>[A-Z])\)', tag.text.strip()).group('alphabet_id')
                        roman_id = re.search('\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('roman_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\) \([A-Z]\)', text.strip()).group(),'')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha=chr(ord(caps_alpha)+1)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{roman_id}"
                        li_tag['class'] = "roman"
                        li_tag.append(ol_tag_for_caps_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{roman_id}{alphabet_id}"
                        ol_tag_for_roman.append(li_tag)
                        roman = fromRoman(ol_id_of_roman.upper())
                        roman += 1
                        roman = toRoman(roman).lower()
                    elif re.search('^\(\d{1,2}\) \([A-Z]\)',tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        ol_id_of_caps_alpha = re.search('\((?P<ol_id_of_caps_alpha>[A-Z])\)', tag.text.strip()).group('ol_id_of_caps_alpha')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\(\d{1,2}\) \([A-Z]\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha=chr(ord(caps_alpha) + 1)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag['class'] = "number"
                        li_tag.append(ol_tag_for_caps_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_caps_alpha}"
                        ol_tag_for_number.append(li_tag)
                        number += 1
                    elif re.search('^\([A-Z]\)', tag.text.strip()):
                        count_of_p_tag=0
                        tag.name = "li"
                        caps_alphabet_id = re.search('^\((?P<caps_alphabet_id>[A-Z])\)', tag.text.strip()).group('caps_alphabet_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\([A-Z]\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))

                        if (caps_roman==caps_alphabet_id and ol_tag_for_caps_alphabet.li) or caps_alpha!=caps_alphabet_id:
                            tag.wrap(ol_tag_for_caps_roman)
                            caps_roman = fromRoman(caps_roman)
                            caps_roman += 1
                            caps_roman = toRoman(caps_roman)
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                            if re.search('^\([A-Z]\)', next_tag.text.strip()):
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                            elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                        else:
                            tag.wrap(ol_tag_for_caps_alphabet)
                            caps_alpha=chr(ord(caps_alpha) + 1)
                            if ol_tag_for_roman.li:
                                id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                            else:
                                id_of_last_li = ol_tag_for_number.find_all("li")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                            if re.search('^[a-z A-Z]+', next_tag.text.strip()):
                                while re.search("^[a-z A-Z]+", next_tag.text.strip()):
                                    sub_tag = next_tag.find_next_sibling()
                                    p_tag = self.soup.new_tag("p")
                                    count_of_p_tag += 1
                                    p_tag.string = next_tag.text
                                    tag.append(p_tag)
                                    id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                                    p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                    p_tag['class']=next_tag['class']
                                    next_tag.decompose()
                                    ol_tag_for_caps_alphabet.append(tag)
                                    next_tag = sub_tag
                                if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha='A'
                                elif re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha='A'
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman='i'
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha='A'
                                elif re.search('^\([a-z]+\)', next_tag.text.strip()):
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman = 'i'
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number=1
                            elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                            elif re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                num_id=re.search('^\((?P<num_id>\d{1,2})\)', next_tag.text.strip()).group('num_id')
                                if str(number)==num_id:
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = 'A'
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman = 'i'
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = 'A'
                                else:
                                    continue
                            elif re.search('^\([a-z]+\)', next_tag.text.strip()):
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman = 'i'
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1

                    elif re.search('^\((XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\)', tag.text.strip()):
                        tag.name = "li"
                        roman_id = re.search('^\((?P<roman_id>(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))\)', tag.text.strip()).group('roman_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\((XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_roman)
                        caps_roman = fromRoman(roman_id)
                        caps_roman += 1
                        caps_roman = toRoman(caps_roman)
                        id_of_last_li=ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                        tag['id'] = f"{id_of_last_li}{roman_id}"
                        if re.search('^\([A-Z]\)', next_tag.text.strip()):
                            alphabet_id=re.search('^\((?P<alphabet_id>[A-Z])\)', next_tag.text.strip()).group('alphabet_id')
                            if (caps_roman==alphabet_id and ol_tag_for_caps_alphabet.li) or caps_alpha!=alphabet_id:
                                continue
                            else:
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman='I'
                        elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                            ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                            ol_tag_for_roman.find_all("li",class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                            caps_roman = 'I'
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                    elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()):
                        tag.name = "li"
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('roman_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)#ol followed by text
                        text = text.replace(re.search('\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', text.strip()).group(),'')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        if (roman_id==roman and ol_tag_for_number.li) or alphabet!=roman_id:
                            tag.wrap(ol_tag_for_roman)
                            roman = fromRoman(roman_id.upper())
                            roman += 1
                            roman = toRoman(roman).lower()
                            tag['class'] = "roman"
                            if ol_tag_for_number.li:
                                id_of_last_li=ol_tag_for_number.find_all("li",class_="number")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{roman_id}"
                            elif ol_tag_for_alphabet.li:
                                id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{roman_id}"
                            if re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name=="br":#5-31.1-1. after 16i 2 break
                                while re.search("^“?[a-z A-Z]+", next_tag.text.strip()):
                                    sub_tag = next_tag.find_next_sibling()
                                    p_tag = self.soup.new_tag("p")
                                    count_of_p_tag += 1
                                    p_tag.string = next_tag.text
                                    tag.append(p_tag)
                                    id_of_last_li = ol_tag_for_roman.find_all("li",class_="roman")[-1].attrs['id']
                                    p_tag['class']=next_tag['class']
                                    p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                    ol_tag_for_roman.append(tag)
                                    next_tag.decompose()
                                    next_tag = sub_tag
                                while next_tag.next_element.name=="br":
                                    sub_tag=next_tag.find_next_sibling()
                                    next_tag.decompose()
                                    next_tag=sub_tag
                            if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha='A'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman='i'
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li",class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman='i'
                            elif re.search('^\([a-z]+\)', next_tag.text.strip()):
                                alphabet_id=re.search('^\((?P<alphabet_id>[a-z]+)\)',next_tag.text.strip()).group('alphabet_id')
                                if alphabet==alphabet_id:
                                    if ol_tag_for_number.li:  # a 1 i
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman='i'
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number=1
                                    elif ol_tag_for_alphabet.li:  # a i
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman='i'
                                else:
                                    continue
                        elif alphabet==roman_id:
                            tag.wrap(ol_tag_for_alphabet)
                            alphabet = chr(ord(alphabet) + 1)
                            tag.attrs['id'] = f"{h3_id}ol{ol_count}{roman_id}"
                            tag['class'] = "alphabet"
                            if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip(),re.IGNORECASE):  # Article 1
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                ol_count=1
                                continue
                            elif re.search('Section \d+', next_tag.text.strip()):
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                if re.search('\(a\)|\(\d\)', next_tag.find_next_sibling().text.strip()):
                                    ol_count += 1
                            elif re.search('^“?[a-z A-Z]+', next_tag.text.strip()):
                                while re.search("^“?[a-z A-Z]+", next_tag.text.strip()) and next_tag.name != "h4":
                                    sub_tag = next_tag.find_next_sibling()
                                    p_tag = self.soup.new_tag("p")
                                    count_of_p_tag += 1
                                    p_tag.string = next_tag.text
                                    tag.append(p_tag)
                                    id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                                    p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                    p_tag['class'] = next_tag['class']
                                    ol_tag_for_alphabet.append(tag)
                                    next_tag.decompose()
                                    next_tag = sub_tag
                                if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                    if ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet='a'
                                if next_tag.name == "h4":
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                            if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                            elif next_tag.name == "h4":
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                        else:
                            tag.wrap(ol_tag_for_inner_roman)
                            inner_roman = fromRoman(roman_id.upper())
                            inner_roman += 1
                            inner_roman = toRoman(inner_roman).lower()
                            if ol_tag_for_inner_number.li:
                                id_of_last_li = ol_tag_for_inner_number.find_all("li")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{roman_id}"
                            elif ol_tag_for_caps_alphabet.li:
                                id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                                tag['id'] = f"{id_of_last_li}{roman_id}"
                            if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                if ol_tag_for_inner_number.li:
                                    ol_tag_for_inner_number.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                    inner_roman = 'i'
                                elif ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                    roman = 'i'
                            elif re.search('^\([A-Z]+\)', next_tag.text.strip()):
                                alphabet_id = re.search('^\((?P<alphabet_id>[A-Z]+)\)', next_tag.text.strip()).group('alphabet_id')
                                if ol_tag_for_inner_number.li:
                                    ol_tag_for_inner_number.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                    ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_number)
                                    ol_tag_for_inner_roman=self.soup.new_tag("ol",type="i")
                                    ol_tag_for_inner_number=self.soup.new_tag("ol")
                                    inner_roman='i'
                                    inner_num=1
                                elif ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                    ol_tag_for_inner_roman=self.soup.new_tag("ol",type="i")
                                    inner_roman='i'
                            else:
                                continue

                    elif re.search('^\([a-z]+\)', tag.text.strip()):
                        count_of_p_tag = 0
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('^\((?P<alphabet_id>[a-z]+)\)', tag.text.strip()).group('alphabet_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\([a-z]+\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        if ol_tag_for_number.li:
                            tag.wrap(ol_tag_for_inner_alphabet)
                            inner_alphabet=chr(ord(inner_alphabet)+1)
                            number_id=ol_tag_for_number.find_all("li",class_="number")[-1].attrs['id']
                            tag.attrs['id'] = f"{number_id}{alphabet_id}"
                        else:
                            tag.wrap(ol_tag_for_alphabet)
                            alphabet = chr(ord(alphabet) + 1)
                            tag.attrs['id'] = f"{h3_id}ol{ol_count}{alphabet_id}"
                            tag['class'] = "alphabet"
                        if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip(),re.IGNORECASE):  # Article 1
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                            ol_count=1
                            continue
                        elif re.search('Section \d+', next_tag.text.strip()):
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                            if re.search('\(a\)|\(\d\)',next_tag.find_next_sibling().text.strip()):
                                ol_count += 1
                        elif re.search('^“?[a-z A-Z]+', next_tag.text.strip()):
                            while re.search("^“?[a-z A-Z]+", next_tag.text.strip()) and next_tag.name != "h4":
                                sub_tag = next_tag.find_next_sibling()
                                p_tag = self.soup.new_tag("p")
                                count_of_p_tag += 1
                                p_tag.string = next_tag.text
                                tag.append(p_tag)
                                id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                                p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                p_tag['class'] = next_tag['class']
                                ol_tag_for_alphabet.append(tag)
                                next_tag.decompose()
                                next_tag = sub_tag
                            if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet='a'
                            elif next_tag.name == "h4":
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                        elif re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                            if ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = 'a'
                        elif next_tag.name == "h4":
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                    elif re.search('^\(\d{1,2}\)', tag.text.strip()):
                        count_of_p_tag=0
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        number_id = re.search('^\((?P<ol_id>\d{1,2})\)', tag.text.strip()).group('ol_id')
                        list_store_text = []
                        for text in tag.contents:#cite_tag
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\(\d{1,2}\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        if str(number)==number_id and ol_tag_for_caps_alphabet.li is None:
                            tag['class'] = "number"
                            if ol_tag_for_alphabet.li:
                                id_of_last_li = ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].attrs['id']#(a) (1)
                                tag['id'] = f"{id_of_last_li}{number_id}"
                            else:
                                tag['id'] = f"{h3_id}ol{ol_count}{number_id}"
                            if ol_tag_for_number.li: #4-13-1
                                ol_tag_for_number.append(tag)
                            else:
                                tag.wrap(ol_tag_for_number)
                            number+=1
                            if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):#roman i
                                roman_id=re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)', next_tag.text.strip()).group('roman_id')
                                if (roman==roman_id and ol_tag_for_number.li) or alphabet!=roman_id:
                                    continue
                                else:
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_number=self.soup.new_tag("ol")
                                    number=1
                            elif re.search('Section \d+',next_tag.text.strip()):
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_alphabet=self.soup.new_tag("ol",type="a")
                                    alphabet='a'
                                ol_tag_for_number=self.soup.new_tag("ol")
                                number=1
                                if re.search('^\(a\)|^\(\d\)',next_tag.find_next_sibling().text.strip()):
                                    ol_count += 1
                            elif re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip()):
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_alphabet=self.soup.new_tag("ol",type="a")
                                    alphabet='a'
                                ol_tag_for_number=self.soup.new_tag("ol")
                                number=1
                                ol_count=1
                            elif re.search('^[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name=="br":
                                if next_tag.find_next_sibling().name=="h4":
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_number=self.soup.new_tag("ol")
                                    number=1
                                else:
                                    while next_tag.name!="h4" and (re.search("^[a-z A-Z]+", next_tag.text.strip()) or next_tag.next_element.name=="br"):#123 text history of section
                                        if next_tag.next_element.name=="br":
                                            sub_tag=next_tag.find_next_sibling()
                                            next_tag.decompose()
                                            next_tag=sub_tag
                                        else:
                                            sub_tag = next_tag.find_next_sibling()
                                            p_tag = self.soup.new_tag("p")
                                            count_of_p_tag+=1
                                            p_tag.string = next_tag.text
                                            tag.append(p_tag)
                                            id_of_last_li=ol_tag_for_number.find_all("li",class_="number")[-1].attrs['id']
                                            p_tag['id']=f"{id_of_last_li}.{count_of_p_tag}"
                                            ol_tag_for_number.append(tag)
                                            next_tag.decompose()
                                            next_tag = sub_tag
                                    if re.search("^\([a-z]+\)",next_tag.text.strip()):
                                        if ol_tag_for_alphabet.li:
                                            ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                        ol_tag_for_number=self.soup.new_tag("ol")
                                        number=1
                                    elif next_tag.name == "h4":
                                        if ol_tag_for_alphabet.li:
                                            ol_tag_for_alphabet.append(ol_tag_for_number)
                                            ol_tag_for_number=self.soup.new_tag("ol")
                                            number=1
                                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                            alphabet='a'
                                        else:
                                            ol_tag_for_number = self.soup.new_tag("ol")
                                            number=1

                            elif re.search('^\([a-z]+\)|^\([a-z]\) \([0-9]\)', next_tag.text.strip()):
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_number=self.soup.new_tag("ol")
                                    number=1
                        else:
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']  # (a) (1)
                            tag['id'] = f"{id_of_last_li}{number_id}"
                            ol_tag_for_inner_number.append(tag)
                            inner_num += 1
                            if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):  # roman i
                                roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',next_tag.text.strip()).group('roman_id')
                                if roman == roman_id and ol_tag_for_number.li:
                                    ol_tag_for_caps_alphabet.append(ol_tag_for_inner_number)
                                    ol_tag_for_roman.append(ol_tag_for_caps_alphabet)
                                else:
                                    continue
                else:
                    if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', tag.text.strip()):
                        tag.name = "li"
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('roman_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        if (roman==roman_id and ol_tag_for_number.li) or alphabet!=roman_id:
                            tag.wrap(ol_tag_for_roman)
                            tag['id'] = ol_tag_for_number.find_all("li")[-1].attrs['id'] + roman_id
                            tag['class']="roman"
                            ol_tag_for_number.find_all("li")[-1].append(ol_tag_for_roman)
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman='i'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number=1

                        else:
                            tag.wrap(ol_tag_for_alphabet)
                            tag.attrs['id'] = f"{h3_id}ol{ol_count}{roman_id}"
                            tag['class'] = "alphabet"
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                    elif re.search('^\([a-z]+\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('^\((?P<ol_id>[a-z]+)\)', tag.text.strip()).group('ol_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text = text.replace(re.search('\([a-z]+\)', text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag.wrap(ol_tag_for_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{alphabet_id}"
                        tag['class'] = "alphabet"
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                        alphabet = 'a'

                    elif re.search('^\(\d{1,2}\)', tag.text.strip()):
                        tag.name = "li"
                        number_id = re.search('^\((?P<ol_id>\d{1,2})\)', tag.text.strip()).group('ol_id')
                        list_store_text = []
                        for text in tag.contents:
                            list_store_text.append(str(text))
                        text = ''.join(list_store_text)
                        text =text.replace(re.search('\(\d{1,2}\)',text.strip()).group(), '')
                        tag.clear()
                        tag.append(BeautifulSoup(text, features="html.parser"))
                        tag['class'] = "number"
                        tag.wrap(ol_tag_for_number)
                        if ol_tag_for_alphabet.li:
                            id_of_last_li=ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{number_id}"
                            ol_tag_for_alphabet.find_all("li",class_="alphabet")[-1].append(ol_tag_for_number)
                        else:
                            tag['id'] = f"{h3_id}ol{ol_count}{number_id}"
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number=1
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                        alphabet='a'
            else:
                continue

    def create_div_tag(self):
        div_tag_for_chapter = self.soup.new_tag("div")
        div_tag_for_section = self.soup.new_tag("div")
        div_tag_for_h4 = self.soup.new_tag("div")
        div_tag_for_h5 = self.soup.new_tag("div")
        div_tag_for_article=self.soup.new_tag("div")
        for tag in self.soup.find_all("h2"):
            next_tag = tag.find_next_sibling()
            tag.wrap(div_tag_for_chapter)
            if next_tag.name == "nav":
                sibling_of_nav = next_tag.find_next_sibling()
                div_tag_for_chapter.append(next_tag)
                next_tag = sibling_of_nav
                if next_tag.name == "h4":
                    sibling_of_h4 = next_tag.find_next_sibling()
                    div_tag_for_h4.append(next_tag)
                    next_tag = sibling_of_h4
                    while next_tag.name == "p":
                        sibling_of_p = next_tag.find_next_sibling()
                        div_tag_for_h4.append(next_tag)
                        next_tag = sibling_of_p
                    div_tag_for_chapter.append(div_tag_for_h4)
                    div_tag_for_h4 = self.soup.new_tag("div")
                if next_tag.name == "h3":
                    tag_of_h3 = next_tag.find_next_sibling()
                    if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',next_tag.text.strip()):
                        next_tag.wrap(div_tag_for_article)
                    else:
                        next_tag.wrap(div_tag_for_section)
                    while tag_of_h3 and tag_of_h3.name != "h2" :
                        if tag_of_h3.name == "h4":
                            tag_of_h4 = tag_of_h3.find_next_sibling()
                            tag_of_h3.wrap(div_tag_for_h4)
                            while tag_of_h4 and tag_of_h4.name != "h4" and tag_of_h4.name != "h2" :
                                if tag_of_h4.name == "h3":
                                    if div_tag_for_h4.next_element:
                                        div_tag_for_section.append(div_tag_for_h4)
                                        div_tag_for_h4 = self.soup.new_tag("div")
                                    if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',tag_of_h4.text.strip()) :
                                        next_tag = tag_of_h4.find_next_sibling()
                                        tag_of_h4.wrap(div_tag_for_article)
                                        tag_of_h4 = next_tag
                                        while tag_of_h4.name == "p" or tag_of_h4.name == "h3":
                                            if tag_of_h4.name == "h3" and re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',tag_of_h4.text.strip()):
                                                next_tag = tag_of_h4.find_next_sibling()
                                                div_tag_for_section.append(div_tag_for_article)
                                                div_tag_for_article = self.soup.new_tag("div")
                                                div_tag_for_article.append(tag_of_h4)
                                                tag_of_h4 = next_tag
                                            elif tag_of_h4['class'][0] == self.dictionary_to_store_class_name['History']:
                                                next_tag = tag_of_h4.find_next_sibling()
                                                div_tag_for_article.append(tag_of_h4)
                                                tag_of_h4 = next_tag
                                            elif tag_of_h4['class'][0] == self.dictionary_to_store_class_name['h4']:
                                                div_tag_for_section.append(div_tag_for_article)
                                                div_tag_for_article = self.soup.new_tag("div")
                                                break
                                        div_tag_for_section.append(div_tag_for_article)
                                        div_tag_for_article = self.soup.new_tag("div")
                                    else:#2-13-1
                                        if div_tag_for_section.next_element:
                                            div_tag_for_chapter.append(div_tag_for_section)
                                        div_tag_for_section = self.soup.new_tag("div")
                                        next_tag = tag_of_h4.find_next_sibling()
                                        div_tag_for_section.append(tag_of_h4)
                                        tag_of_h4 = next_tag
                                        if tag_of_h4.name == "p":
                                            next_tag = tag_of_h4.find_next_sibling()
                                            div_tag_for_section.append(tag_of_h4)
                                            tag_of_h4 = next_tag

                                elif tag_of_h4.name == "h5":
                                    tag_of_h5 = tag_of_h4.find_next_sibling()
                                    tag_of_h4.wrap(div_tag_for_h5)
                                    while tag_of_h5.name != "h5" and tag_of_h5.name != "h3":
                                        if tag_of_h5.next_element.name == "br":
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5 = self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                            div_tag_for_section.append(tag_of_h5)
                                            tag_of_h5 = next_tag
                                        elif tag_of_h5.name == "h4":
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5 = self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                            break
                                        elif tag_of_h5.name == "h2":
                                            div_tag_for_chapter.append(div_tag_for_section)
                                            div_tag_for_section = self.soup.new_tag("div")
                                            div_tag_for_chapter = self.soup.new_tag("div")
                                            break
                                        else:
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h5.append(tag_of_h5)
                                            tag_of_h5 = next_tag
                                    if div_tag_for_h5.next_element:
                                        div_tag_for_h4.append(div_tag_for_h5)
                                    div_tag_for_h5 = self.soup.new_tag("div")
                                    tag_of_h4 = tag_of_h5
                                elif tag_of_h4.next_element.name == "br":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(div_tag_for_h4)
                                    div_tag_for_h4 = self.soup.new_tag("div")
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                    if tag_of_h4.name == "h2":
                                        div_tag_for_chapter.append(div_tag_for_section)
                                        div_tag_for_section = self.soup.new_tag("div")
                                        div_tag_for_chapter = self.soup.new_tag("div")
                                elif tag_of_h4.name == "nav":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_h4.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                elif tag_of_h4.name == "ol":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                elif tag_of_h4.name=="p":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    if tag_of_h4.text.isupper():#after article caps title
                                        if div_tag_for_h4.next_element:
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4=self.soup.new_tag("div")
                                        div_tag_for_section.append(tag_of_h4)
                                    else:
                                        if div_tag_for_h4.next_element:
                                            div_tag_for_h4.append(tag_of_h4)
                                        else:
                                            div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag

                            if div_tag_for_h4.next_element:
                                div_tag_for_section.append(div_tag_for_h4)
                                div_tag_for_h4 = self.soup.new_tag("div")
                        elif tag_of_h3.name == "h3" and re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',tag_of_h3.text.strip()):
                            next_tag=tag_of_h3.find_next_sibling()
                            div_tag_for_article.append(tag_of_h3)
                            tag_of_h3=next_tag
                            #chapter 24
                            while tag_of_h3.name!="h3" and  tag_of_h3.name!="h4":
                                next_tag = tag_of_h3.find_next_sibling()
                                div_tag_for_article.append(tag_of_h3)
                                tag_of_h3 = next_tag
                            div_tag_for_section.append(div_tag_for_article)
                            div_tag_for_article=self.soup.new_tag("div")
                        else:
                            next_tag = tag_of_h3.find_next_sibling()
                            div_tag_for_section.append(tag_of_h3)
                        tag_of_h3 = next_tag

                    if div_tag_for_section.next_element:
                        div_tag_for_chapter.append(div_tag_for_section)
                        div_tag_for_section=self.soup.new_tag("div")
                        div_tag_for_chapter=self.soup.new_tag("div")

    def remove_class_name(self):
        for tag in self.soup.find_all():
            if tag.name not in ["ul","li","h2"]:
                del tag['class']

    def adding_css_to_file(self):
        head_tag = self.soup.find("head")
        link_tag = self.soup.new_tag("link", rel="stylesheet",href="https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css")
        head_tag.append(link_tag)

    def write_to_file(self):
        file_write = open("/home/mis/PycharmProjects/practice/venv/ricode/modified/gov.ri.code.title.03.html", "w")
        file_write.write(self.soup.prettify())

html_file = "/home/mis/PycharmProjects/practice/venv/ricode/raw/gov.ri.code.title.03.html"
unstructured_to_structured_html = UnstructuredHtmlToStructuredHtml(html_file)
unstructured_to_structured_html.get_class_name()
unstructured_to_structured_html.remove_junk()
unstructured_to_structured_html.convert_to_header_and_assign_id()
unstructured_to_structured_html.create_nav_and_ul_tag()
unstructured_to_structured_html.create_nav_and_main_tag()
unstructured_to_structured_html.add_citation()
unstructured_to_structured_html.create_ol_tag()
unstructured_to_structured_html.create_div_tag()
unstructured_to_structured_html.remove_class_name()
unstructured_to_structured_html.adding_css_to_file()
unstructured_to_structured_html.write_to_file()

