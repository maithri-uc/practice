"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""

import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns, CustomisedRegexRI
import roman
from loguru import logger


class RIParseHtml(ParseHtml, RegexPatterns):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):

        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES',
                'ul': r'^Preamble', 'head2': '^Article I',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_i': '^—', 'head4': r'Compiler’s Notes\.|Repealed Sections\.', 'history': r'History of Section\.|Cross References\.'}

            self.h2_order = ['article', '', '', '', '']
            self.h2_text_con: list = ['Articles of Amendment', 'Rhode Island Constitution Translation Table']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+[A-Z]?(\.\d+)?', 'ul': r'^Chapters? \d+(\.\d+)?(\.\d+)?([A-Z])?',
                                        'head2': r'^Chapters? \d+(\.\d+)?(\.\d+)?([A-Z])?', 'history': r'History of Section\.|Cross References\.',
                                        'head4': r'Compiler’s Notes\.|Repealed Sections\.',
                                        'head3': r'^\d+[A-Z]?(\.\d+)?-\d+(-\d+)?(([A-Z])(-\d+)?)?(\.\d+(-\d+)?(\.\d+((\.\d+)?\.\d+)?)?(-\d+)?)?|^Chs\.\s*\d+\s*-\s*\d+\.',
                                        'junk1': '^Text|^Annotations',  'ol_of_i': r'\([A-Z a-z0-9]\)'}

            file_no = re.search(r'gov\.ri\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if file_no in ['02', '07', '31', '44']:
                self.h2_order = ['chapter', 'part', '', '', '']
            elif file_no in ['06A']:
                self.h2_order = ['chapter', 'part', 'subpart', '', '']
            elif file_no in ['21', '42', '34']:
                self.h2_order = ['chapter', 'article', '', '', '']
            elif file_no in ['15', '23']:
                self.h2_order = ['chapter', 'article', 'part', '', '']
            else:
                self.h2_order = ['chapter', '', '', '', '']
            self.h2_pattern_text: list = [r'^(?P<tag>C)hapters (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)']
        self.h4_head: list = ['Compiler’s Notes.', 'Compiler\'s Notes.', 'Variations from Uniform Code.', 'Obsolete Sections.', 'Omitted Sections.', 'Reserved Sections.', 'Compiler\'s Notes', 'Cross References.', 'Subsequent Reenactments.', 'Abridged Life Tables and Tables of Work Life Expectancies.', 'Definitional Cross References.', 'Contingent Effective Dates.', 'Applicability.', 'Comparative Legislation.', 'Sunset Provision.', 'Liberal Construction.', 'Sunset Provisions.', 'Legislative Findings.', 'Contingently Repealed Sections.', 'Transferred Sections.', 'Collateral References.', 'NOTES TO DECISIONS', 'Retroactive Effective Dates.', 'Legislative Intent.', 'Repealed Sections.', 'Effective Dates.', 'Law Reviews.', 'Rules of Court.', 'OFFICIAL COMMENT', 'Superseded Sections.', 'Repeal of Sunset Provision.', 'Legislative Findings and Intent.', 'Official Comment.', 'Official Comments', 'Repealed and Reenacted Sections.', 'COMMISSIONER’S COMMENT', 'Comment.', 'History of Amendment.', 'Ratification.', 'Federal Act References.', 'Reenactments.', 'Severability.', 'Delayed Effective Dates.', 'Delayed Effective Date.', 'Delayed Repealed Sections.']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']

        self.watermark_text = """Release {0} of the Official Code of Rhode Island Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexRI()

    def recreate_tag(self, p_tag):
        new_tag = self.soup.new_tag("p")
        text = p_tag.b.text
        new_tag.string = text
        new_tag['class'] = p_tag['class']
        p_tag.insert_before(new_tag)
        p_tag.string = re.sub(f'{text}', '', p_tag.text.strip())
        return p_tag, new_tag

    def replace_tags_titles(self):
        """
            - regex_pattern_obj  for customised regex class is created
            - h2_order list which has order of h2 tags created
            - calling method of base class
            - replacing all other tags which are not handled in the base class

        """
        super(RIParseHtml, self).replace_tags_titles()
        h4_count = 1
        h5count = 1
        note_to_decision_list: list = []
        note_to_decision_id: list = []
        case_tag = None
        count = 1
        inner_case_tag = None
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^NOTES TO DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["history"]]:
                            tag.name = "li"
                            tag["class"] = "note"
                            note_to_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and not re.search(r'Collateral References\.', tag.b.text):
                            if tag.text.strip() in note_to_decision_list:
                                if re.search(r'^—\s*\w+', tag.text.strip()):
                                    tag.name = "h5"
                                    inner_case_tag = tag
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    tag_inner_id = f'{case_tag.get("id")}-{tag_text}'

                                    if tag_inner_id in note_to_decision_id:
                                        tag["id"] = f'{tag_inner_id}.{count:02}'
                                        count += 1
                                    else:
                                        tag["id"] = tag_inner_id
                                        count = 1
                                    note_to_decision_id.append(tag_inner_id)

                                elif re.search(r'^— —\s*\w+', tag.text.strip()):
                                    tag.name = "h5"
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    tag_inner1_id = f'{inner_case_tag.get("id")}-{tag_text}'

                                    if tag_inner1_id in note_to_decision_id:
                                        tag["id"] = f'{tag_inner1_id}.{count:02}'
                                        count += 1
                                    else:
                                        tag["id"] = tag_inner1_id
                                        count = 1
                                    note_to_decision_id.append(tag_inner1_id)
                                else:
                                    tag.name = "h5"
                                    case_tag = tag
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    tag_id = f'{tag.find_previous("h3").get("id")}-notetodecision-{tag_text}'

                                    if tag_id in note_to_decision_id:
                                        tag["id"] = f'{tag_id}.{h5count:02}'
                                        h5count += 1
                                    else:
                                        tag["id"] = f'{tag_id}'
                                        h5count = 1
                                    note_to_decision_id.append(tag_id)
                            else:
                                tag.name = "h5"
                                case_tag = tag
                                tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                tag_id = f'{tag.find_previous("h3").get("id")}-notetodecision-{tag_text}'

                                if tag_id in note_to_decision_id:
                                    tag["id"] = f'{tag_id}.{h5count:02}'
                                    h5count += 1
                                else:
                                    tag["id"] = f'{tag_id}'
                                    h5count = 1
                                note_to_decision_id.append(tag_id)
                        elif tag.name in ["h2", "h3", "h4"]:
                            break

            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["ul"]]:
                    p_tag.name = "li"
                    p_tag.wrap(self.ul_tag)
                elif p_tag.get("class") == [self.tag_type_dict["history"]]:
                    if re.search(r"^History of Section\.", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', new_tag.text.strip()).lower()
                        new_tag.attrs['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"
                    elif re.search('The Interstate Compact on Juveniles', p_tag.text.strip()):
                        p_tag.name = "h4"
                        p_tag['id'] = f"{p_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{re.sub(r'[^a-zA-Z0-9]', '', p_tag.text).lower()}"
                    elif re.search(r"^ARTICLE (\d+|[IVXCL]+)", p_tag.text.strip(), re.IGNORECASE):
                        if re.search(r"^ARTICLE [IVXCL]+\.?$", p_tag.text.strip()):
                            p_tag.name = "h4"
                            article_id = re.search(r"^ARTICLE (?P<article_id>([IVXCL]+|\d+))", p_tag.text.strip(),re.IGNORECASE).group('article_id')
                            p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_id}"
                        elif re.search(r"^ARTICLE [IVXCL]+\.?[A-Z\sa-z]+", p_tag.text.strip(), re.IGNORECASE) and p_tag.name != "li":  # article notes to dceision
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search('^(ARTICLE (?P<article_id>[IVXCL]+))', p_tag.text.strip(), re.IGNORECASE)
                            if p_tag.b:
                                tag_for_article.string = p_tag.b.text
                                tag_text = re.sub(fr'{p_tag.b.text}', '', p_tag.text.strip())
                            else:
                                tag_for_article.string = article_number.group()
                                tag_text = re.sub(fr'{article_number.group()}', '', p_tag.text.strip())
                            p_tag.insert_before(tag_for_article)
                            p_tag.clear()
                            p_tag.string = tag_text
                            tag_for_article.attrs['class'] = [self.tag_type_dict['history']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_id')}"
                        # elif re.search(r'^Article [IVXCL]+\.[A-Z a-z]+', p_tag.text.strip()):
                        #     p_tag.name = "h4"
                        #     article_number = re.search('^(Article (?P<article_id>[IVXCL]+))', p_tag.text.strip())
                        #     p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_id')}"
                        elif re.search(r'^Article [IVXCL]+\.$', p_tag.text.strip()):
                            p_tag.name = 'li'
                        elif re.search(r'^Article \d+\.', p_tag.text.strip()):
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search(r'^(Article (?P<article_number>\d+)\.)', p_tag.text.strip())
                            tag_for_article.string = article_number.group()
                            tag_text = p_tag.text.replace(f'{article_number.group()}', '')
                            p_tag.insert_before(tag_for_article)
                            p_tag.clear()
                            p_tag.string = tag_text
                            tag_for_article.attrs['class'] = [self.tag_type_dict['history']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_number')}"
                        else:
                            p_tag.name = "h4"
                            article_id = re.search(r"^ARTICLE (?P<article_id>([IVXCL]+|\d+))", p_tag.text.strip(),re.IGNORECASE).group('article_id')
                            p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_id}"
                            print(p_tag)

                    elif re.search(r"^Section \d+. [a-z ,\-A-Z]+\. \(a\)", p_tag.text.strip()) and re.search(r"^\(b\)", p_tag.find_next_sibling().text.strip()):
                        text_from_b = p_tag.text.split('(a)')
                        p_tag_for_section = self.soup.new_tag("p")
                        p_tag_for_section.string = text_from_b[0]
                        text = p_tag.text.strip()
                        text = f"{text.replace(f'{text_from_b[0]}', '')}"
                        p_tag.string = text
                        p_tag.insert_before(p_tag_for_section)
                        p_tag_for_section.attrs['class'] = p_tag['class']
                    elif re.search(r'^Schedule [IVX]+', p_tag.text.strip()):
                        p_tag.name = "h4"
                        p_tag['class'] = 'schedule'
                        schedule_id = re.search(r'^Schedule (?P<schedule_id>[IVX]+)', p_tag.text.strip()).group('schedule_id')
                        p_tag.attrs['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}sec{schedule_id}"
                elif p_tag.get('class') == [self.tag_type_dict["head2"]]:
                    if re.search(r'^Chapters? (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)', p_tag.text.strip()):
                        p_tag.name = "h2"
                elif p_tag.get('class') == [self.tag_type_dict["head4"]]:
                    if re.search(r'^Cross References\.\s+[a-zA-Z0-9]+|^Compiler’s Notes\.\s+[a-zA-Z0-9]+|^Definitional Cross References[.:]\s+[“a-z A-Z0-9]+', p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        header4_tag_text = re.sub(r'[\W.]+', '', new_tag.text.strip()).lower()
                        h4_tag_id = f'{new_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'
                        if h4_tag_id in self.h4_cur_id_list:
                            new_tag['id'] = f'{h4_tag_id}.{h4_count}'
                            h4_count += 1
                        else:
                            new_tag['id'] = f'{h4_tag_id}'
                        self.h4_cur_id_list.append(h4_tag_id)
                    elif re.search(r'^Purposes( of Changes( and New Matter)?)?\. (\d+|\([a-z]\))', p_tag.text.strip()):
                        self.recreate_tag(p_tag)
            elif p_tag.name == "h2" and p_tag.get("class") == "oneh2":
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    @staticmethod
    def add_p_tag_to_li(tag, next_tag, count_of_p_tag):
        sub_tag = next_tag.find_next_sibling()
        next_tag['id'] = f"{tag['id']}.{count_of_p_tag}"
        tag.append(next_tag)
        next_tag['class'] = "text"
        count_of_p_tag += 1
        next_tag = sub_tag
        return next_tag, count_of_p_tag

    @staticmethod
    def decompose_tag(next_tag):
        sub_tag = next_tag.find_next_sibling()
        next_tag.decompose()
        return sub_tag

    def split_tag(self, tag, split_attr):
        text_from_b = tag.text.split(split_attr)
        p_tag = self.soup.new_tag("p")
        if split_attr in ['.', ':']:
            p_tag.string = f'{text_from_b[0]}{split_attr}'
            tag.string = tag.text.replace(f'{text_from_b[0]}{split_attr}', '')
        else:
            p_tag.string = f'{text_from_b[0]}:'
            tag.string = tag.text.replace(f'{text_from_b[0]}:', '')
        tag.insert_before(p_tag)
        p_tag.attrs['class'] = tag['class']

    def recreate_ol_tag(self):
        for tag in self.soup.main.find_all(["p"]):
            class_name = tag['class'][0]
            if class_name == self.tag_type_dict['history'] or class_name == self.tag_type_dict['ol_of_i'] or class_name == self.tag_type_dict['head4']:
                if re.search(r'^\(\w\)\s[A-Za-z,; ]+\.\s*\(\w\)', tag.text.strip(), re.IGNORECASE) and tag.b:
                    self.split_tag(tag, '.')
                elif re.search(r'^[A-Za-z ]+:\s*\(\w\)', tag.text.strip(), re.IGNORECASE):
                    self.split_tag(tag, ':')
                elif re.search(r'^\(([a-zA-Z]|\d+)\)\s(\(\w\) )?.+:\s\(\w\)', tag.text.strip()):
                    text = re.search(r'^\(([a-zA-Z]|\d+)\)\s(\((?P<id>\w)\) )?.+:\s\((?P<text>\w)\)', tag.text.strip())
                    alpha = text.group('id')
                    text = text.group('text')
                    text_string = text
                    if text in ['a', 'A']:
                        text = chr(ord(text) + 1)
                    elif text == '1':
                        text = int(text)+1
                    elif text == 'i':
                        text = roman.fromRoman(text.upper())
                        text += 1
                        text = roman.toRoman(text).lower()
                    elif text == 'I':
                        text = roman.fromRoman(text)
                        text += 1
                        text = roman.toRoman(text)
                    if re.search(fr'^\({text}\)', tag.find_next_sibling().text.strip()) and alpha != text_string:
                        self.split_tag(tag, f': ({text_string})')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        self.recreate_ol_tag()
        alphabet = 'a'
        number = 1
        roman_number = 'i'
        inner_roman = 'i'
        caps_alpha = 'A'
        inner_num = 1
        caps_roman = 'I'
        inner_alphabet = 'a'
        ol_count = 1
        ol_tag_for_roman = self.soup.new_tag("ol", type='i')
        ol_tag_for_number = self.soup.new_tag("ol")
        ol_tag_for_alphabet = self.soup.new_tag("ol", type='a')
        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
        ol_tag_for_inner_number = self.soup.new_tag("ol")
        ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
        ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
        inner_caps_roman = 'I'
        count_of_p_tag = 1
        id_of_last_li = None
        for tag in self.soup.main.find_all(["h2", "h3", "h4", "p", "h5"]):
            if not tag.name:
                continue
            class_name = tag['class'][0]
            if class_name == self.tag_type_dict['history'] or class_name == self.tag_type_dict['ol_of_i'] or class_name == self.tag_type_dict['head4']:
                if re.search("^“?[a-z A-Z]+", tag.text.strip()):
                    next_sibling = tag.find_next_sibling()
                    if next_sibling and tag.name == "h3":
                        ol_count = 1
                if tag.i:
                    tag.i.unwrap()
                next_tag = tag.find_next_sibling()
                if not next_tag:  # last tag
                    break
                if next_tag.next_element.name and next_tag.next_element.name == 'br':
                    next_tag.decompose()
                    next_tag = tag.find_next_sibling()

                if re.search(fr'^\([gk]\)', tag.text.strip()) and self.input_file_name == "gov.ri.code.title.19.html" and tag.find_previous_sibling().get('class') == "h3_part":
                    alphabet = re.search(fr'^\((?P<alpha_id>[gk])\)', tag.text.strip()).group('alpha_id')
                    if alphabet == "g":
                        start = 7
                    else:
                        start = 11
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a", start=start)
                if re.search(fr'^{number}\.', tag.text.strip()):
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^{number}\.', '', tag.text.strip())
                    tag['class'] = "number"
                    if ol_tag_for_caps_alphabet.li:
                        tag[
                            'id'] = f"{ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1].attrs['id']}{number}"
                    elif ol_tag_for_alphabet.li:
                        tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{number}"
                    else:
                        tag['id'] = f"{tag_id}ol{ol_count}{number}"
                    tag.wrap(ol_tag_for_number)
                    number += 1
                    while (next_tag.name != "h2" and next_tag.name != "h4" and next_tag.name != "h3") and (
                            re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name == "br"):
                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                            next_tag = self.decompose_tag(next_tag)
                        elif re.search(fr'^{caps_alpha}{caps_alpha}?\.|^{inner_alphabet}\.', next_tag.text.strip()):
                            break
                        else:
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                    count_of_p_tag = 1
                    if next_tag.name == "h3" or next_tag.name == "h4" or next_tag.name == "h2":
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number = 1
                        ol_count = 1
                    elif re.search(fr'^{caps_alpha}{caps_alpha}?\.|^\({caps_alpha}{caps_alpha}?\)',
                                   next_tag.text.strip()):
                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(ol_tag_for_number)
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number = 1
                    elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()) and ol_tag_for_alphabet.li:
                        if ol_tag_for_caps_alphabet.li:
                            ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(ol_tag_for_number)
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            if ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                            else:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                    ol_tag_for_caps_alphabet)
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                        else:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                elif re.search(fr'^{caps_alpha}{caps_alpha}?\.', tag.text.strip()):
                    tag.name = "li"
                    caps_alpha_id = re.search(fr'^(?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\.',
                                              tag.text.strip()).group('caps_alpha_id')
                    tag.string = re.sub(fr'^{caps_alpha}{caps_alpha}?\.', '', tag.text.strip())
                    tag['class'] = "caps_alpha"

                    if re.search('[IVX]+', caps_alpha_id):
                        caps_alpha_id = f'-{caps_alpha_id}'
                    else:
                        caps_alpha_id = caps_alpha
                    tag['id'] = f"{tag.find_previous({'h5', 'h4', 'h3'}).get('id')}ol{ol_count}{caps_alpha_id}"
                    tag.wrap(ol_tag_for_caps_alphabet)
                    caps_alpha = chr(ord(caps_alpha) + 1)
                    while (next_tag.name != "h2" and next_tag.name != "h4" and next_tag.name != "h3") and (
                            re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name == "br"):
                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                            next_tag = self.decompose_tag(next_tag)
                        elif re.search(fr'^{caps_alpha}{caps_alpha}?\.', next_tag.text.strip()):
                            break
                        else:
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                    count_of_p_tag = 1
                    if next_tag.name == "h3" or next_tag.name == "h4" or next_tag.name == "h2":
                        if ol_tag_for_number.li:
                            ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(ol_tag_for_number)
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                        caps_alpha = 'A'
                        ol_count = 1
                elif re.search(fr'^{inner_alphabet}\.', tag.text.strip()):
                    tag.name = "li"
                    tag.string = re.sub(fr'^{inner_alphabet}\.', '', tag.text.strip())
                    tag['class'] = "inner_alpha"
                    if ol_tag_for_number.li:
                        tag['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{inner_alphabet}'
                    tag.wrap(ol_tag_for_inner_alphabet)
                    inner_alphabet = chr(ord(inner_alphabet) + 1)
                    while (next_tag.name != "h2" and next_tag.name != "h4" and next_tag.name != "h3") and (
                            re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name == "br"):
                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                            next_tag = self.decompose_tag(next_tag)
                        elif re.search(fr'^{inner_alphabet}{inner_alphabet}?\.', next_tag.text.strip()):
                            break
                        else:
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                    count_of_p_tag = 1
                    if re.search(fr'^{number}\.', next_tag.text.strip()):
                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        inner_alphabet = 'a'
                    elif next_tag.name == "h3" or next_tag.name == "h4" or next_tag.name == "h2":
                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        inner_alphabet = 'a'
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number = 1
                        ol_count = 1
                elif re.search(fr'^\({caps_alpha}{caps_alpha}?\)', tag.text.strip()) and caps_roman != 'II':
                    if re.search(fr'^\({caps_alpha}{caps_alpha}?\) \({caps_roman}\)', tag.text.strip()):
                        if re.search(fr'^\({caps_alpha}{caps_alpha}?\) \({caps_roman}\) \({inner_alphabet}\)',
                                     tag.text.strip()):
                            tag.name = "li"
                            caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                      tag.text.strip()).group('caps_alpha_id')
                            if re.search('[IVX]+', caps_alpha_id):
                                caps_alpha_id = f'-{caps_alpha_id}'
                            tag.string = re.sub(
                                fr'^\({caps_alpha}{caps_alpha}?\) \({caps_roman}\) \({inner_alphabet}\)',
                                '', tag.text.strip())
                            tag.wrap(ol_tag_for_inner_alphabet)
                            li_tag_for_caps_alpha = self.soup.new_tag("li")
                            li_tag_for_caps_alpha['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                            li_tag_for_caps_roman = self.soup.new_tag("li")
                            li_tag_for_caps_roman['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{caps_roman}"
                            li_tag_for_caps_alpha['class'] = "caps_alpha"
                            tag.attrs[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{caps_roman}{inner_alphabet}"
                            tag['class'] = "inner_alpha"
                            li_tag_for_caps_roman['class'] = "caps_roman"
                            li_tag_for_caps_roman.append(ol_tag_for_inner_alphabet)
                            ol_tag_for_caps_roman.append(li_tag_for_caps_roman)
                            li_tag_for_caps_alpha.append(ol_tag_for_caps_roman)
                            ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                            caps_roman = roman.fromRoman(caps_roman)
                            caps_roman += 1
                            caps_roman = roman.toRoman(caps_roman)
                            if caps_alpha == 'Z':
                                caps_alpha = 'A'
                            else:
                                caps_alpha = chr(ord(caps_alpha) + 1)
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                        else:
                            tag.name = "li"

                            caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                      tag.text.strip()).group('caps_alpha_id')
                            if re.search('[IVX]+', caps_alpha_id):
                                caps_alpha_id = f'-{caps_alpha_id}'
                            tag.string = re.sub(fr'^\({caps_alpha}{caps_alpha}?\) \({caps_roman}\)', '',
                                                tag.text.strip())
                            tag.wrap(ol_tag_for_caps_roman)
                            li_tag_for_caps_alpha = self.soup.new_tag("li")
                            if ol_tag_for_roman.li:
                                li_tag_for_caps_alpha['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{caps_alpha_id}"
                                tag.attrs['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{caps_alpha_id}-{caps_roman}"
                            else:
                                li_tag_for_caps_alpha['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                                tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{caps_roman}"
                            li_tag_for_caps_alpha['class'] = "caps_alpha"
                            tag['class'] = "caps_roman"
                            li_tag_for_caps_alpha.append(ol_tag_for_caps_roman)
                            ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                            caps_roman = roman.fromRoman(caps_roman)
                            caps_roman += 1
                            caps_roman = roman.toRoman(caps_roman)
                            if caps_alpha == 'Z':
                                caps_alpha = 'A'
                            else:
                                caps_alpha = chr(ord(caps_alpha) + 1)
                    elif re.search(fr'^\({caps_alpha}{caps_alpha}?\) \({inner_num}\)', tag.text.strip()):
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                  tag.text.strip()).group('caps_alpha_id')
                        tag.string = re.sub(fr'^\({caps_alpha}{caps_alpha}?\) \({inner_num}\)', '', tag.text.strip())
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.wrap(ol_tag_for_inner_number)
                        li_tag_for_caps_alpha = self.soup.new_tag("li")
                        if ol_tag_for_roman.li:
                            li_tag_for_caps_alpha[
                                'id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{caps_alpha_id}"
                            tag.attrs[
                                'id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{caps_alpha_id}{inner_num}"
                        else:
                            li_tag_for_caps_alpha[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                            tag.attrs[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}{inner_num}"
                        li_tag_for_caps_alpha['class'] = "caps_alpha"
                        tag['class'] = "inner_num"
                        li_tag_for_caps_alpha.append(ol_tag_for_inner_number)
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                        inner_num += 1
                        if caps_alpha == 'Z':
                            caps_alpha = 'A'
                        else:
                            caps_alpha = chr(ord(caps_alpha) + 1)
                        if re.search(fr'^\({roman_number}\)', next_tag.text.strip()):
                            ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                ol_tag_for_inner_number)
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_inner_number = self.soup.new_tag("ol")
                            inner_num = 1
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                    elif re.search(fr'^\({caps_alpha}{caps_alpha}?\) \({inner_roman}\)', tag.text.strip()):
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                  tag.text.strip()).group('caps_alpha_id')
                        tag.string = re.sub(fr'^\({caps_alpha}{caps_alpha}?\) \({inner_roman}\)', '', tag.text.strip())
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.wrap(ol_tag_for_inner_roman)
                        li_tag_for_caps_alpha = self.soup.new_tag("li")
                        if ol_tag_for_number.li:
                            li_tag_for_caps_alpha[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                            tag.attrs[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{inner_roman}"
                        else:
                            li_tag_for_caps_alpha[
                                'id'] = f"{tag.find_previous({'h5', 'h4', 'h3'}).get('id')}ol{ol_count}{caps_alpha_id}"
                            tag[
                                'id'] = f"{tag.find_previous({'h5', 'h4', 'h3'}).get('id')}ol{ol_count}{caps_alpha_id}-{inner_roman}"
                        li_tag_for_caps_alpha['class'] = "caps_alpha"
                        tag['class'] = "inner_roman"
                        li_tag_for_caps_alpha.append(ol_tag_for_inner_roman)
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                        inner_roman = roman.fromRoman(inner_roman.upper())
                        inner_roman += 1
                        inner_roman = roman.toRoman(inner_roman).lower()
                        if caps_alpha == 'Z':
                            caps_alpha = 'A'
                        else:
                            caps_alpha = chr(ord(caps_alpha) + 1)
                    elif re.search(fr'^\({caps_alpha}{caps_alpha}?\) \({roman_number}\)', tag.text.strip()):
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                  tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.string = re.sub(fr'^\({caps_alpha}{caps_alpha}?\) \({roman_number}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_roman)
                        li_tag_for_caps_alpha = self.soup.new_tag("li")
                        if ol_tag_for_number.li:
                            li_tag_for_caps_alpha[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                            tag.attrs[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{roman_number}"
                        li_tag_for_caps_alpha['class'] = "caps_alpha"
                        tag['class'] = "roman"
                        li_tag_for_caps_alpha.append(ol_tag_for_roman)
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        if caps_alpha == 'Z':
                            caps_alpha = 'A'
                        else:
                            caps_alpha = chr(ord(caps_alpha) + 1)
                    else:
                        if caps_alpha == "I" and re.search(r'^\(II\)', next_tag.text.strip()):
                            if re.search(fr'^\({caps_roman}\)', tag.text.strip()):
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({caps_roman}\)', '', tag.text.strip())
                                if ol_tag_for_caps_roman.li:
                                    ol_tag_for_caps_roman.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_caps_roman)
                                if ol_tag_for_inner_roman.li:
                                    tag['id'] = f"{ol_tag_for_inner_roman.find_all('li', class_='inner_roman')[-1].attrs['id']}-{caps_roman}"
                                elif ol_tag_for_caps_alphabet.li:
                                    tag['id'] = f"{ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1].attrs['id']}-{caps_roman}"
                                elif ol_tag_for_roman.li:
                                    tag['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}-{caps_roman}"
                                elif ol_tag_for_number.li:
                                    tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}-{caps_roman}"
                                tag['class'] = "caps_roman"
                                caps_roman = roman.fromRoman(caps_roman)
                                caps_roman += 1
                                caps_roman = roman.toRoman(caps_roman)
                                while (re.search("^[a-z A-Z]+",
                                                 next_tag.text.strip()) or next_tag.next_element.name == "br") and next_tag.name != "h4" and next_tag.name != "h3":
                                    if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                        next_tag = self.decompose_tag(next_tag)
                                    else:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                count_of_p_tag = 1
                                if re.search(fr'^\({caps_alpha}{caps_alpha}?\)', next_tag.text.strip()) and re.search(
                                        fr'^\((?P<caps_id>{caps_alpha}{caps_alpha}?)\)', next_tag.text.strip()).group('caps_id') != "II":
                                    if ol_tag_for_inner_roman.li:
                                        ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_inner_roman)
                                        ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                        inner_roman = "i"
                                    else:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_caps_roman)
                                    ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                    caps_roman = 'I'
                                elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()) and roman_number != "i":
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = 'A'
                                    else:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                elif re.search(fr'^\({number}\)', next_tag.text.strip()):
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_caps_roman)
                                        if ol_tag_for_roman.li:
                                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = "i"
                                        else:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = 'A'
                                    elif ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'

                                elif re.search(fr'^\({inner_alphabet}\)',
                                               next_tag.text.strip()) and inner_alphabet != "a":
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                elif next_tag.name == "h4":
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_caps_roman)
                                        if ol_tag_for_roman.li:
                                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = "i"
                                        else:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = 'A'
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                    elif ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                    ol_count = 1
                            else:
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({inner_caps_roman}\)', '', tag.text.strip())
                                if ol_tag_for_inner_caps_roman.li:
                                    ol_tag_for_inner_caps_roman.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_inner_caps_roman)
                                if ol_tag_for_roman.li:
                                    id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']

                                tag['id'] = f"{id_of_last_li}-{inner_caps_roman}"
                                tag['class'] = "inner_caps_roman"
                                inner_caps_roman = roman.fromRoman(inner_caps_roman)
                                inner_caps_roman += 1
                                inner_caps_roman = roman.toRoman(inner_caps_roman)
                                while re.search("^[a-z A-Z]+",
                                                next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                count_of_p_tag = 1
                                if re.search(fr'^\({number}\)', next_tag.text.strip()):
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                        ol_tag_for_inner_caps_roman)
                                    if ol_tag_for_caps_roman.li:
                                        ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_caps_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = 'I'
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
                                    inner_caps_roman = 'I'
                        else:
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                            if re.search('[IVX]+', caps_alpha_id):
                                caps_alpha_id = f'-{caps_alpha_id}'
                            tag.string = re.sub(fr'^\({caps_alpha}{caps_alpha}?\)', '', tag.text.strip())
                            tag['class'] = "caps_alpha"
                            tag.wrap(ol_tag_for_caps_alphabet)
                            if ol_tag_for_roman.li:
                                tag['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{caps_alpha_id}"
                            elif ol_tag_for_number.li:
                                tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                            else:
                                tag['id'] = f"{tag_id}ol{ol_count}{caps_alpha_id}"
                            if caps_alpha == "Z":
                                caps_alpha = 'A'
                            else:
                                caps_alpha = chr(ord(caps_alpha) + 1)
                            while (re.search(r"^“?(\*\*)?[a-z A-Z]+|^\*“?[A-Za-z ]+|^\((ix|iv|v?i{0,3})\)|^\(\d+\)|^\([A-Z]+\)", next_tag.text.strip()) or next_tag.next_element.name == "br") and next_tag.name != "h4" and next_tag.name != "h3":
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search(r'^\((ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                    roman_id = re.search(r'^\((?P<roman_id>(ix|iv|v?i{0,3}))\)',
                                                         next_tag.text.strip()).group('roman_id')
                                    if roman_id != roman_number and roman_id != inner_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break

                                elif re.search(r'^\([A-Z]+\)', next_tag.text.strip()):
                                    caps_id = re.search(r'^\((?P<caps_id>[A-Z]+)\)', next_tag.text.strip()).group(
                                        'caps_id')
                                    if caps_id[0] != caps_alpha and caps_id != caps_roman and caps_id != inner_caps_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                    number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number_id != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                else:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                            if re.search(fr'^\({inner_roman}\)', next_tag.text.strip()) and ol_tag_for_caps_alphabet.li:
                                continue
                            elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()):
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                            elif re.search(fr'^\({number}\)|^{number}\.', next_tag.text.strip()) and number != 1:
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    if ol_tag_for_inner_alphabet.li:
                                        ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_inner_alphabet)
                                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                        inner_alphabet = "a"
                                    elif ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = 'i'
                                else:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                            elif re.search(fr'^\({inner_alphabet}\)', next_tag.text.strip()) and ol_tag_for_number.li:
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                        ol_tag_for_roman)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = 'i'
                            elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    if ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = 'i'
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                    else:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = 'i'
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                else:
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                            elif next_tag.name == "h4" or next_tag.name == "h3":
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    if ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        if ol_tag_for_alphabet.li:
                                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                                ol_tag_for_number)
                                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                            alphabet = 'a'
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                    else:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = 'a'
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = 'a'
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                else:
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = 'A'
                                ol_count = 1
                elif re.search(fr'^\({caps_roman}\)|^\({inner_caps_roman}\)', tag.text.strip()):
                    if re.search(fr'^\({caps_roman}\)', tag.text.strip()):
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({caps_roman}\)', '', tag.text.strip())
                        if ol_tag_for_caps_roman.li:
                            ol_tag_for_caps_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_caps_roman)
                        if ol_tag_for_inner_roman.li:
                            id_of_last_li = ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].attrs['id']
                        elif ol_tag_for_caps_alphabet.li:
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].attrs['id']
                        elif ol_tag_for_roman.li:
                            id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                        elif ol_tag_for_number.li:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                        tag['id'] = f"{id_of_last_li}-{caps_roman}"
                        tag['class'] = "caps_roman"
                        caps_roman = roman.fromRoman(caps_roman)
                        caps_roman += 1
                        caps_roman = roman.toRoman(caps_roman)
                        while (re.search("^[a-z A-Z]+",
                                         next_tag.text.strip()) or next_tag.next_element.name == "br") and next_tag.name != "h4" and next_tag.name != "h3":
                            if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                next_tag = self.decompose_tag(next_tag)
                            else:
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                        count_of_p_tag = 1
                        if re.search(fr'^\({caps_alpha}{caps_alpha}?\)',
                                     next_tag.text.strip()) and f'{caps_alpha}{caps_alpha}?' != "II":
                            if ol_tag_for_inner_roman.li:
                                ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].append(
                                    ol_tag_for_caps_roman)
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = "i"
                            else:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_caps_roman)
                            ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                            caps_roman = 'I'
                        elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()) and roman_number != "i":
                            if ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_caps_roman)
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                            else:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                        elif re.search(fr'^\({number}\)', next_tag.text.strip()):
                            if ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_caps_roman)
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                else:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                            elif ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'

                        elif re.search(fr'^\({inner_alphabet}\)', next_tag.text.strip()) and inner_alphabet != "a":
                            if ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                    ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                        elif next_tag.name == "h4":
                            if ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_caps_roman)
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                else:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                            elif ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                            ol_count = 1
                    else:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({inner_caps_roman}\)', '', tag.text.strip())
                        if ol_tag_for_inner_caps_roman.li:
                            ol_tag_for_inner_caps_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_caps_roman)
                        if ol_tag_for_roman.li:
                            id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']

                        tag['id'] = f"{id_of_last_li}-{inner_caps_roman}"
                        tag['class'] = "inner_caps_roman"
                        inner_caps_roman = roman.fromRoman(inner_caps_roman)
                        inner_caps_roman += 1
                        inner_caps_roman = roman.toRoman(inner_caps_roman)
                        while re.search("^[a-z A-Z]+",
                                        next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                        count_of_p_tag = 1
                        if re.search(fr'^\({number}\)', next_tag.text.strip()):
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                ol_tag_for_inner_caps_roman)
                            if ol_tag_for_caps_roman.li:
                                ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(ol_tag_for_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                caps_roman = 'I'
                            else:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
                            inner_caps_roman = 'I'
                elif re.search(fr'^\({roman_number}\)|^\({inner_roman}\)', tag.text.strip()) and (
                        ol_tag_for_number.li or alphabet != roman_number) and inner_roman != inner_alphabet:
                    if re.search(fr'^\({roman_number}\) \({caps_alpha}{caps_alpha}?\)', tag.text.strip()):
                        caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                  tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({roman_number}\) \({caps_alpha}{caps_alpha}?\)', '', tag.text.strip())
                        tag['class'] = "caps_alpha"
                        tag.wrap(ol_tag_for_caps_alphabet)
                        li_tag = self.soup.new_tag("li")
                        if ol_tag_for_number.li:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                        elif ol_tag_for_alphabet.li:
                            id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                        li_tag['id'] = f"{id_of_last_li}-{roman_number}"
                        li_tag['class'] = "roman"
                        li_tag.append(ol_tag_for_caps_alphabet)
                        tag.attrs['id'] = f"{id_of_last_li}-{roman_number}{caps_alpha_id}"
                        if caps_alpha == 'Z':
                            caps_alpha = 'A'
                        else:
                            caps_alpha = chr(ord(caps_alpha) + 1)
                        ol_tag_for_roman.append(li_tag)
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                    elif re.search(fr'^\({inner_roman}\)', tag.text.strip()) and inner_roman != inner_alphabet and (
                            ol_tag_for_caps_alphabet.li or ol_tag_for_inner_number.li):
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({inner_roman}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_inner_roman)
                        tag['class'] = "inner_roman"
                        if ol_tag_for_inner_alphabet.li:
                            id_of_last_li = ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].attrs[
                                'id']
                        elif ol_tag_for_inner_number.li:
                            id_of_last_li = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].attrs['id']
                        elif ol_tag_for_caps_roman.li:
                            id_of_last_li = ol_tag_for_caps_roman.find_all("li")[-1].attrs['id']
                        elif ol_tag_for_caps_alphabet.li:
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].attrs['id']
                        elif ol_tag_for_roman.li:
                            id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                        tag['id'] = f"{id_of_last_li}-{inner_roman}"
                        inner_roman = roman.fromRoman(inner_roman.upper())
                        inner_roman += 1
                        inner_roman = roman.toRoman(inner_roman).lower()
                        while re.search("^[a-z A-Z]+",
                                        next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                        count_of_p_tag = 1
                        if re.search(fr'^\({inner_num}\)', next_tag.text.strip()) and inner_num != 1:
                            if ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                if ol_tag_for_inner_number.li:
                                    ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                            elif ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_roman)
                            ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                            inner_roman = 'i'
                        elif re.search(fr'^\({number}\)', next_tag.text.strip()) and number != 1:
                            if ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = "A"
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = "A"
                                elif ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                            elif ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = "A"
                                else:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = "A"
                        elif re.search(fr'^\({caps_alpha}{caps_alpha}?\)', next_tag.text.strip()):
                            if ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                if ol_tag_for_inner_number.li:
                                    ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_inner_number)
                                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                                        inner_num = 1
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = 'a'
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                            elif ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                            elif ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                        elif re.search(fr'^\({alphabet}{alphabet}?\)',
                                       next_tag.text.strip()) and alphabet != 'a' and inner_roman != "ii" and roman_number != "ii":
                            if ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = "A"
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = "A"
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                else:
                                    if ol_tag_for_roman.li:
                                        ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                            ol_tag_for_inner_number)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = "i"
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                                        inner_num = 1
                            elif ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = "A"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                else:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_caps_alphabet)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = "A"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                        elif re.search(fr'\({caps_roman}\)', next_tag.text.strip()) and caps_roman != "I":

                            ol_tag_for_caps_roman.find_all("li")[-1].append(ol_tag_for_inner_roman)
                            ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                            inner_roman = "i"
                    else:
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({roman_number}\)', '', tag.text.strip())
                        if ol_tag_for_roman.li:
                            ol_tag_for_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_roman)
                        tag['class'] = "roman"
                        if ol_tag_for_inner_alphabet.li:
                            tag['id'] = f"{ol_tag_for_inner_alphabet.find_all('li', class_='inner_alpha')[-1].attrs['id']}-{roman_number}"

                        elif ol_tag_for_caps_roman.li:
                            tag['id'] = f"{ol_tag_for_caps_roman.find_all('li', class_='caps_roman')[-1].attrs['id']}-{roman_number}"

                        elif ol_tag_for_number.li:
                            tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}-{roman_number}"

                        elif ol_tag_for_alphabet.li:
                            tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}-{roman_number}"
                        else:
                            tag['id'] = f"{tag_id}ol{ol_count}-{roman_number}"
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        while next_tag.name != "h4" and next_tag.name != "h3" and (re.search(r'^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\(\d+\)|^\([a-z]+\)', next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                            if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                next_tag = self.decompose_tag(next_tag)
                            elif re.search(r"^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\([a-z]+\)|^\(\d+\)", next_tag.text.strip()):
                                if re.search(fr'^{inner_alphabet}{inner_alphabet}?\.', next_tag.text.strip()):
                                    break
                                elif re.search(r'^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                    roman_id = re.search(r'^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',
                                                         next_tag.text.strip()).group('roman_id')
                                    if roman_id != roman_number and roman_id != alphabet:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(r"^“?[a-z A-Z]+|^\[[A-Z a-z]+|^\([\w ]{4,}", next_tag.text.strip()):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)

                                elif re.search(r"^\([A-Z]{1,2}\)", next_tag.text.strip()):
                                    alpha_id = re.search(r"^\((?P<alpha_id>[A-Z]+)\)", next_tag.text.strip()).group(
                                        'alpha_id')
                                    if alpha_id[0] != caps_alpha and alpha_id != caps_roman and alpha_id != inner_caps_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(r"^\([a-z]{1,2}\)", next_tag.text.strip()):
                                    alpha_id = re.search(r"^\((?P<alpha_id>[a-z]+)\)", next_tag.text.strip()).group(
                                        'alpha_id')
                                    if alpha_id[0] != alphabet and alpha_id[0] != inner_alphabet:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                    number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number_id != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                        count_of_p_tag = 1
                        if re.search(fr'^\({number}\)', next_tag.text.strip()) and number != 1:
                            if ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                    ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                            elif ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                    ol_tag_for_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                            elif ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                        elif re.search(fr'^\({caps_alpha}{caps_alpha}?\)',
                                       next_tag.text.strip()) and ol_tag_for_caps_alphabet.li:
                            ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(ol_tag_for_roman)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = "i"
                        elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()) and ol_tag_for_number.li:
                            continue
                        elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()) and alphabet != "a":
                            if ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                    ol_tag_for_number)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                            elif ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                    ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                        elif re.search(fr'^\({inner_alphabet}\)|^{inner_alphabet}{inner_alphabet}?\.', next_tag.text.strip()) and inner_alphabet != 'a':
                            ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(ol_tag_for_roman)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = "i"
                        elif next_tag.name == "h4" or next_tag.name == "h3":
                            if ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                    ol_tag_for_roman)
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = "a"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                            elif ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = "a"
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                            elif ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = "a"
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = "i"
                            ol_count = 1
                elif re.search(fr'^\({alphabet}{alphabet}?\)|^\({inner_alphabet}\)', tag.text.strip()) and (inner_roman != "ii" and roman_number != "ii"):
                    if re.search(fr'^\({alphabet}{alphabet}?\)\s?\({number}\)', tag.text.strip()):
                        if re.search(fr'^\({alphabet}{alphabet}?\) \({number}\) \({roman_number}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({alphabet}{alphabet}?\) \({number}\) \({roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_number.append(ol_tag_for_roman)
                            ol_tag_for_number.append(li_tag_for_number)
                            li_tag_for_alphabet.append(ol_tag_for_number)
                            ol_tag_for_alphabet.append(li_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}-{roman_number}"
                            tag['class'] = "roman"
                            number += 1
                            alphabet = chr(ord(alphabet) + 1)
                            roman_number = roman.fromRoman(roman_number.upper())
                            roman_number += 1
                            roman_number = roman.toRoman(roman_number).lower()
                            while re.search("^[a-z A-Z]+",
                                            next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                        elif re.search(fr'^\({alphabet}{alphabet}?\) \({number}\) \({inner_alphabet}\)',
                                       tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({alphabet}{alphabet}?\) \({number}\) \({inner_alphabet}\)', '',
                                                tag.text.strip())
                            tag.wrap(ol_tag_for_inner_alphabet)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_number.append(ol_tag_for_inner_alphabet)
                            ol_tag_for_number.append(li_tag_for_number)
                            li_tag_for_alphabet.append(ol_tag_for_number)
                            ol_tag_for_alphabet.append(li_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}-{inner_alphabet}"
                            tag['class'] = "inner_alpha"
                            number += 1
                            alphabet = chr(ord(alphabet) + 1)
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                            while re.search("^[a-z A-Z]+",
                                            next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                        elif re.search(fr'^\({alphabet}{alphabet}?\) \({number}\) \({caps_alpha}{caps_alpha}?\)',
                                       tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            if re.search('[IVX]+', caps_alpha):
                                caps_alpha_id = f'-{caps_alpha}'
                            else:
                                caps_alpha_id = caps_alpha
                            tag.string = re.sub(
                                fr'^\({alphabet}{alphabet}?\) \({number}\) \({caps_alpha}{caps_alpha}?\)', '',
                                tag.text.strip())
                            tag.wrap(ol_tag_for_caps_alphabet)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_number.append(ol_tag_for_caps_alphabet)
                            ol_tag_for_number.append(li_tag_for_number)
                            li_tag_for_alphabet.append(ol_tag_for_number)
                            ol_tag_for_alphabet.append(li_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alphabet}{number}{caps_alpha_id}"
                            tag['class'] = "caps_alpha"
                            number += 1
                            alphabet = chr(ord(alphabet) + 1)
                            caps_alpha = chr(ord(caps_alpha) + 1)
                            while re.search("^[a-z A-Z]+",
                                            next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                        else:
                            alpha_id = re.search(fr'^\((?P<alpha_id>{alphabet}{alphabet}?)\)', tag.text.strip()).group(
                                'alpha_id')
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)\s?\({number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_number)
                            li_tag = self.soup.new_tag("li")
                            li_tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                            li_tag['class'] = "alphabet"
                            ol_tag_for_number.wrap(li_tag)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}{number}"
                            tag['class'] = "number"
                            li_tag.wrap(ol_tag_for_alphabet)
                            number += 1
                            alphabet = chr(ord(alphabet) + 1)
                            while (re.search(r"^[a-z A-Z]+|^\([\w ]{4,}",
                                             next_tag.text.strip()) or next_tag.next_element.name == "br") and next_tag.name != "h4" and next_tag.name != "h3":
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                else:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                            if re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()) and not re.search(
                                    r'^\(ii\)', next_tag.find_next_sibling().text.strip()):
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                    elif re.search(fr'^\({alphabet}{alphabet}?\) \({roman_number}\)',
                                   tag.text.strip()) and not ol_tag_for_number.li:
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({alphabet}{alphabet}?\) \({roman_number}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_roman)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{tag_id}ol{ol_count}{alphabet}"
                        li_tag['class'] = "alphabet"
                        ol_tag_for_roman.wrap(li_tag)
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{alphabet}-{roman_number}"
                        tag['class'] = "roman"
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_alphabet)
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        alphabet = chr(ord(alphabet) + 1)
                    elif re.search(fr'^\({alphabet}{alphabet}?\)', tag.text.strip()) and (
                            not ol_tag_for_number.li and not ol_tag_for_caps_alphabet.li and not ol_tag_for_inner_number.li):
                        alpha_id = re.search(fr'^\((?P<alpha_id>{alphabet}{alphabet}?)\)', tag.text.strip()).group(
                            'alpha_id')
                        if alphabet == "i" and re.search(fr'^\({caps_alpha}{caps_alpha}?\)', next_tag.text.strip()):
                            sibling_of_i = tag.find_next_sibling(
                                lambda sibling_tag: re.search(r'^\(ii\)|^History of Section\.',
                                                              sibling_tag.text.strip()))
                            if re.search(r'^\(ii\)', sibling_of_i.text.strip()):
                                if re.search(fr'^\({roman_number}\) \({caps_alpha}{caps_alpha}?\)', tag.text.strip()):
                                    caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                              tag.text.strip()).group('caps_alpha_id')
                                    if re.search('[IVX]+', caps_alpha_id):
                                        caps_alpha_id = f'-{caps_alpha_id}'
                                    tag.name = "li"
                                    tag.string = re.sub(fr'^\({roman_number}\) \({caps_alpha}{caps_alpha}?\)', '',
                                                        tag.text.strip())
                                    tag['class'] = "caps_alpha"
                                    tag.wrap(ol_tag_for_caps_alphabet)
                                    li_tag = self.soup.new_tag("li")
                                    if ol_tag_for_number.li:
                                        id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs[
                                            'id']
                                    elif ol_tag_for_alphabet.li:
                                        id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                                    li_tag['id'] = f"{id_of_last_li}-{roman_number}"
                                    li_tag['class'] = "roman"
                                    li_tag.append(ol_tag_for_caps_alphabet)
                                    tag.attrs['id'] = f"{id_of_last_li}-{roman_number}{caps_alpha_id}"
                                    if caps_alpha == 'Z':
                                        caps_alpha = 'A'
                                    else:
                                        caps_alpha = chr(ord(caps_alpha) + 1)
                                    ol_tag_for_roman.append(li_tag)
                                    roman_number = roman.fromRoman(roman_number.upper())
                                    roman_number += 1
                                    roman_number = roman.toRoman(roman_number).lower()
                                else:
                                    tag.name = "li"
                                    tag.string = re.sub(fr'^\({roman_number}\)', '', tag.text.strip())
                                    tag.wrap(ol_tag_for_roman)
                                    tag['class'] = "roman"
                                    if ol_tag_for_number.li:
                                        tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}-{roman_number}"
                                    elif ol_tag_for_alphabet.li:
                                        tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}-{roman_number}"
                                    roman_number = roman.fromRoman(roman_number.upper())
                                    roman_number += 1
                                    roman_number = roman.toRoman(roman_number).lower()
                                    while (re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or (
                                            next_tag.next_element and next_tag.next_element.name == "br")) and next_tag.name != "h4" and next_tag.name != "h3":
                                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                            next_tag = self.decompose_tag(next_tag)
                                        elif re.search("^“?[a-z A-Z]+",
                                                       next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                            count_of_p_tag)
                                    count_of_p_tag = 1
                                    if re.search(fr'^\({number}\)', next_tag.text.strip()):
                                        if ol_tag_for_caps_alphabet.li:
                                            ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                            caps_alpha = 'A'
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = 'i'
                                        elif ol_tag_for_number.li:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = 'i'
                                    elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()):
                                        continue
                                    elif re.search(fr'^\({alphabet}{alphabet}?\)',
                                                   next_tag.text.strip()) and alphabet != "a":
                                        if ol_tag_for_number.li:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                                ol_tag_for_number)
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = 'i'
                                            ol_tag_for_number = self.soup.new_tag("ol")
                                            number = 1
                                        elif ol_tag_for_alphabet.li:
                                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                                ol_tag_for_roman)
                                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                            roman_number = 'i'
                            else:
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)', '', tag.text.strip())
                                tag[
                                    'id'] = f"{tag.find_previous({'h5', 'h4', 'h3'}).get('id')}ol{ol_count}{alpha_id}"
                                tag.wrap(ol_tag_for_alphabet)
                                if alphabet == "z":
                                    alphabet = 'a'
                                else:
                                    alphabet = chr(ord(alphabet) + 1)
                                tag['class'] = "alphabet"
                                while (next_tag.name != "h4" and next_tag.name != "h3" and not re.search(
                                        r'^ARTICLE [IVXCL]+|^Section \d+|^[IVXCL]+. Purposes\.', next_tag.text.strip(),
                                        re.IGNORECASE)) and (re.search(r'^“?(\*\*)?[a-z A-Z]+|^_______________|^\[[A-Z a-z]+|^\(\d+\)', next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                                    if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                        next_tag = self.decompose_tag(next_tag)

                                    elif re.search(fr'^\(\d+\)', next_tag.text.strip()):
                                        number_id = re.search(fr'^\((?P<number_id>\d+)\)',
                                                              next_tag.text.strip()).group('number_id')
                                        if number_id != str(number) and number != str(inner_num):
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                            count_of_p_tag)
                                        else:
                                            break
                                    else:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                count_of_p_tag = 1

                                if re.search(r'^[IVXCL]+. Purposes\.', next_tag.text.strip()):
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                                    ol_count += 1
                                elif re.search(r'^Section \d+', next_tag.text.strip()):
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                                    if re.search(r'\(a\)|\(\d\)', next_tag.find_next_sibling().text.strip()):
                                        ol_count += 1
                                elif next_tag.name == "h4" or next_tag.name == "h3":
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                                    ol_count = 1
                        else:

                            tag.name = "li"
                            tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)', '', tag.text.strip())
                            tag.attrs['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{alpha_id}"
                            tag.wrap(ol_tag_for_alphabet)
                            if alphabet == "z":
                                alphabet = 'a'
                            else:
                                alphabet = chr(ord(alphabet) + 1)
                            tag['class'] = "alphabet"
                            while (next_tag.name != "h4" and next_tag.name != "h3" and not re.search(
                                    r'^ARTICLE [IVXCL]+^ARTICLE [IVXCL]+|^Section \d+|^[IVXCL]+. Purposes\.|^Part [IVXCL]+',
                                    next_tag.text.strip(), re.IGNORECASE)) and (re.search(r'^“?(\*\*)?[a-z A-Z]+|^_______________|^\[[A-Z a-z]+|^\(\d+\)|^\([\w ]{4,}', next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search(fr'^\(\d+\)', next_tag.text.strip()):
                                    number_id = re.search(fr'^\((?P<number_id>\d+)\)', next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(r'^\([a-z]{1,2}\)', next_tag.text.strip()):
                                    alphabet_id = re.search(r'^\((?P<alphabet_id>([a-z]+))\)',
                                                            next_tag.text.strip()).group('alphabet_id')
                                    if alphabet_id[0] != alphabet and alphabet_id[0] != inner_alphabet and alphabet_id != roman_number and alphabet_id != inner_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                else:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                            if re.search('^Part [IVXCL]+', next_tag.text.strip(),
                                         re.IGNORECASE):
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                ol_count = 1
                                if re.search('^Part [IVXCL]+', next_tag.text.strip()):
                                    next_tag['class'] = "h3_part"
                            elif re.search(r'^[IVXCL]+. Purposes\.', next_tag.text.strip()):
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                ol_count += 1
                            elif re.search(r'^Section \d+', next_tag.text.strip()):
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                if re.search(r'\(a\)|\(\d\)', next_tag.find_next_sibling().text.strip()):
                                    ol_count += 1
                            elif next_tag.name == "h4" or next_tag.name == "h3":
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                ol_count = 1
                    else:
                        if re.search(fr'^\({inner_alphabet}\) \({roman_number}\)', tag.text.strip()):
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({inner_alphabet}\) \({roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag = self.soup.new_tag("li")
                            li_tag[
                                'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{inner_alphabet}"
                            li_tag['class'] = "inner_alpha"
                            ol_tag_for_roman.wrap(li_tag)
                            tag.attrs[
                                'id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{inner_alphabet}-{roman_number}'
                            tag['class'] = "roman"
                            if ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.append(li_tag)
                            else:
                                li_tag.wrap(ol_tag_for_inner_alphabet)
                            roman_number = roman.fromRoman(roman_number.upper())
                            roman_number += 1
                            roman_number = roman.toRoman(roman_number).lower()
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                        else:
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({inner_alphabet}\)', '', tag.text.strip())
                            if ol_tag_for_inner_alphabet.li:
                                ol_tag_for_inner_alphabet.append(tag)
                            else:
                                tag.wrap(ol_tag_for_inner_alphabet)
                            id_of_alpha = None
                            if ol_tag_for_inner_roman.li:
                                id_of_alpha = ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].attrs[
                                    'id']
                            elif ol_tag_for_caps_roman.li:
                                id_of_alpha = ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].attrs['id']
                            elif ol_tag_for_inner_number.li:
                                id_of_alpha = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].attrs['id']
                            elif ol_tag_for_roman.li:
                                id_of_alpha = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                            elif ol_tag_for_number.li:
                                id_of_alpha = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag.attrs['id'] = f"{id_of_alpha}{inner_alphabet}"
                            tag['class'] = "inner_alpha"
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                            while (re.search(r'^“?[a-z A-Z]+|^\(\d+\)', next_tag.text.strip()) or (
                                    next_tag.next_element and next_tag.next_element.name == "br")) and next_tag.name != "h4" and next_tag.name != "h3":
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search("^“?[a-z A-Z]+",
                                               next_tag.text.strip()) and next_tag.name != "h4" and next_tag.name != "h3":
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                    number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number_id != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                            count_of_p_tag = 1
                            if re.search(fr'^\({inner_num}\)', next_tag.text.strip()) and inner_num != 1:
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                            elif re.search(fr'^\({number}\)|^{number}\.', next_tag.text.strip()) and number != 1:
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = 'a'
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = 'a'
                            elif re.search(fr'^\({inner_roman}\)', next_tag.text.strip()) and inner_roman != "i":
                                ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].append(
                                    ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = 'a'
                            elif re.search(fr'^\({caps_roman}\)', next_tag.text.strip()) and caps_roman != 'I':
                                ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(
                                    ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                            elif re.search(fr'^\({caps_alpha}{caps_alpha}?\)', next_tag.text.strip()):
                                ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                    ol_tag_for_inner_alphabet)
                                ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                    ol_tag_for_inner_number)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                            elif re.search(fr'^\({inner_alphabet}\)',
                                           next_tag.text.strip()) and inner_alphabet == alphabet:
                                sibling_of_alpha = next_tag.find_next_sibling(
                                    lambda sibling_tag: re.search(r'^\([1-9]\)|^\(ii\)', sibling_tag.text.strip()))
                                if ol_tag_for_alphabet.li and re.search(fr'^\(1\)', sibling_of_alpha.text.strip()):
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = "a"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                else:
                                    continue
                            elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = "a"
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                            elif next_tag.name == "h4" or next_tag.name == "h3":
                                if ol_tag_for_caps_roman.li:
                                    ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_caps_roman)
                                        if ol_tag_for_number.li:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_caps_alphabet)
                                            if ol_tag_for_alphabet.li:
                                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                                    ol_tag_for_number)
                                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                                alphabet = "a"
                                                ol_tag_for_number = self.soup.new_tag("ol")
                                                number = 1
                                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                            caps_alpha = "A"
                                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                        caps_roman = "I"
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = "a"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                elif ol_tag_for_inner_number.li:
                                    ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1].append(
                                        ol_tag_for_inner_alphabet)
                                    if ol_tag_for_caps_alphabet.li:
                                        ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                            ol_tag_for_inner_number)
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        caps_alpha = "A"
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = 'a'
                                ol_count = 1
                elif re.search(fr'^\({number}\)|^\({inner_num}\)', tag.text.strip()):
                    if re.search(fr'^\({number}\) \({inner_alphabet}\) \({roman_number}\)', tag.text.strip()):
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({number}\) \({alphabet}{alphabet}?\) \({roman_number}\)', '',
                                            tag.text.strip())
                        tag.wrap(ol_tag_for_roman)
                        li_tag_for_number = self.soup.new_tag("li")
                        li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{number}"
                        li_tag_for_number['class'] = "number"
                        li_tag_for_inner_alphabet = self.soup.new_tag("li")
                        li_tag_for_inner_alphabet['id'] = f"{tag_id}ol{ol_count}{number}{inner_alphabet}"
                        li_tag_for_inner_alphabet['class'] = "inner_alpha"
                        ol_tag_for_roman.wrap(li_tag_for_inner_alphabet)
                        li_tag_for_inner_alphabet.wrap(ol_tag_for_inner_alphabet)
                        ol_tag_for_inner_alphabet.wrap(li_tag_for_number)
                        li_tag_for_number.wrap(ol_tag_for_number)
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}{inner_alphabet}-{roman_number}"
                        tag['class'] = "roman"
                        number += 1
                        inner_alphabet = chr(ord(inner_alphabet) + 1)
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                    elif re.search(fr'^\({number}\)\s?\({roman_number}\)', tag.text.strip()):
                        if re.search(fr'^\({number}\) \({roman_number}\) \({caps_alpha}{caps_alpha}?\)',
                                     tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')

                            caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                      tag.text.strip()).group('caps_alpha_id')
                            if re.search('[IVX]+', caps_alpha_id):
                                caps_alpha_id = f'-{caps_alpha_id}'
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\) \({roman_number}\) \({caps_alpha}{caps_alpha}?\)', '',
                                                tag.text.strip())
                            tag.wrap(ol_tag_for_caps_alphabet)
                            tag['class'] = "caps_alpha"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{number}"
                            li_tag_for_roman = self.soup.new_tag("li")
                            li_tag_for_roman['id'] = f"{tag_id}ol{ol_count}{number}-{roman_number}"
                            li_tag_for_number['class'] = "number"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}-{roman_number}{caps_alpha_id}"
                            li_tag_for_roman['class'] = "roman"
                            li_tag_for_roman.append(ol_tag_for_caps_alphabet)
                            ol_tag_for_roman.append(li_tag_for_roman)
                            li_tag_for_number.append(ol_tag_for_roman)
                            ol_tag_for_number.append(li_tag_for_number)
                            number += 1
                            roman_number = roman.fromRoman(roman_number.upper())
                            roman_number += 1
                            roman_number = roman.toRoman(roman_number).lower()
                            if caps_alpha == 'Z':
                                caps_alpha = 'A'
                            else:
                                caps_alpha = chr(ord(caps_alpha) + 1)
                        else:
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\)\s?\({roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag = self.soup.new_tag("li")
                            li_tag['class'] = "number"
                            ol_tag_for_roman.wrap(li_tag)
                            if ol_tag_for_alphabet.li:
                                tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{number}-{roman_number}"
                                li_tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{number}"
                            else:
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}-{roman_number}"
                                li_tag['id'] = f"{tag_id}ol{ol_count}{number}"
                            roman_number = roman.fromRoman(roman_number.upper())
                            roman_number += 1
                            roman_number = roman.toRoman(roman_number).lower()
                            tag['class'] = "roman"
                            if ol_tag_for_number.li:
                                ol_tag_for_number.append(li_tag)
                            else:
                                li_tag.wrap(ol_tag_for_number)
                            number += 1

                            while next_tag.name != "h4" and next_tag.name != "h3" and (
                                    re.search(r'^“?[a-z A-Z]+|^\(\d+\)', next_tag.text.strip()) or (
                                    next_tag.next_element and next_tag.next_element.name == "br")):
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search("^“?[a-z A-Z]+", next_tag.text.strip()):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                    number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number_id != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                            count_of_p_tag = 1
                            if re.search(fr'^\({number}\)', next_tag.text.strip()):
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = "i"
                    elif re.search(fr'^\({number}\) \({inner_alphabet}\)', tag.text.strip()):
                        if re.search(fr'^\({number}\) \({inner_alphabet}\) \({roman_number}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\) \({inner_alphabet}\) \({roman_number}\)', '',
                                                tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_inner_alphabet = self.soup.new_tag("li")
                            li_tag_for_inner_alphabet['id'] = f"{tag_id}ol{ol_count}{number}{inner_alphabet}"
                            li_tag_for_inner_alphabet['class'] = "inner_alpha"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}{inner_alphabet}-{roman_number}"
                            li_tag_for_inner_alphabet.append(ol_tag_for_roman)
                            ol_tag_for_inner_alphabet.append(li_tag_for_inner_alphabet)
                            li_tag_for_number.append(ol_tag_for_inner_alphabet)
                            ol_tag_for_number.append(li_tag_for_number)
                            number += 1
                            roman_number = roman.fromRoman(roman_number.upper())
                            roman_number += 1
                            roman_number = roman.toRoman(roman_number).lower()
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                        elif re.search(fr'^\({number}\) \({inner_alphabet}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\) \({inner_alphabet}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_inner_alphabet)
                            li_tag = self.soup.new_tag("li")
                            li_tag['id'] = f"{tag_id}ol{ol_count}{number}"
                            li_tag['class'] = "number"
                            li_tag.append(ol_tag_for_inner_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}{inner_alphabet}"
                            tag['class'] = "inner_alpha"
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                            ol_tag_for_number.append(li_tag)
                            number += 1
                            if re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                                inner_alphabet = 'a'
                    elif re.search(fr'^\({number}\) \({caps_alpha}{caps_alpha}?\)', tag.text.strip()):
                        caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{caps_alpha}{caps_alpha}?)\)',
                                                  tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({number}\) \({caps_alpha}{caps_alpha}?\)', '', tag.text.strip())
                        tag['class'] = "caps_alpha"
                        li_tag = self.soup.new_tag("li")
                        if ol_tag_for_alphabet.li:
                            li_tag[
                                'id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{number}'
                            tag.attrs[
                                'id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{number}{caps_alpha_id}'
                        else:
                            li_tag['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{number}"
                            tag.attrs[
                                'id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{number}{caps_alpha_id}"
                        li_tag['class'] = "number"
                        tag.wrap(ol_tag_for_caps_alphabet)
                        li_tag.append(ol_tag_for_caps_alphabet)

                        if caps_alpha == 'Z':
                            caps_alpha = 'A'
                        else:
                            caps_alpha = chr(ord(caps_alpha) + 1)
                        ol_tag_for_number.append(li_tag)
                        number += 1
                    elif re.search(fr'^\({number}\)', tag.text.strip()) and inner_num == 1 and not ol_tag_for_roman.li and not ol_tag_for_caps_alphabet.li:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({number}\)', '', tag.text.strip())
                        tag['class'] = "number"
                        if ol_tag_for_alphabet.li:
                            tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{number}"
                        elif ol_tag_for_caps_alphabet.li:
                            tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='caps_alpha')[-1].attrs['id']}{number}"
                        else:
                            tag['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{number}"

                        if ol_tag_for_number.li:
                            ol_tag_for_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_number)
                        number += 1
                        while next_tag.name != "h4" and next_tag.name != "h5" and next_tag.name != "h3" and (re.search(
                                r"^\([\w ]{4,}|^“\([A-Z a-z]+\)|^\. \. \.|^\[[A-Z a-z]+|^“?[a-z A-Z]+|^_______________|^\((ix|iv|v?i{0,3})\)|^\(\d+\)|^\([a-z]+\)|^\([A-Z ]+\)",
                                next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                            if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                next_tag = self.decompose_tag(next_tag)
                            elif re.search(r"^\([\w ]{4,}|^“\([A-Z a-z]+\)|^_______________|^\. \. \.|^\([a-z]+\)|^“?[a-z A-Z]+|^\[[A-Z a-z]+|^\(\d+\)|^\((ix|iv|v?i{0,3})\)|^\([A-Z ]+\) ", next_tag.text.strip()):
                                if re.search(r'^Section \d+', next_tag.text.strip()):
                                    break
                                elif re.search(r'^\([a-z]{1,2}\)', next_tag.text.strip()):
                                    alphabet_id = re.search(r'^\((?P<alphabet_id>([a-z]+))\)',
                                                            next_tag.text.strip()).group('alphabet_id')
                                    if alphabet_id[0] != alphabet and alphabet_id[0] != inner_alphabet and alphabet_id != roman_number and alphabet_id != inner_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                                elif re.search(
                                        r"^\([\w ]{4,}|^“\([A-Z a-z]+\)|^_______________|^\. \. \.|^\[[A-Z a-z]+|^“?[a-z A-Z]+",
                                        next_tag.text.strip()):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                elif re.search(r'^\(\d+\)', next_tag.text.strip()):
                                    number_id = re.search(r'^\((?P<number_id>(\d+))\)', next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number_id != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break

                                elif re.search(r'^\([A-Z ]{1,2}\) ', next_tag.text.strip()):
                                    alphabet_id = re.search(r'^\((?P<alphabet_id>([A-Z ]+))\)',
                                                            next_tag.text.strip()).group('alphabet_id')
                                    if alphabet_id != caps_alpha and alphabet_id != caps_roman and alphabet_id != inner_caps_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                        count_of_p_tag = 1
                        if re.search(r'^Section \d+', next_tag.text.strip()):
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            if re.search(r'^\(a\)|^\(\d\)', next_tag.find_next_sibling().text.strip()):
                                ol_count += 1
                        elif re.search('^ARTICLE [IVXCL]+', next_tag.text.strip()):
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            ol_count = 1
                        elif re.search(fr'^\({alphabet}{alphabet}?\) \(1\) \({roman_number}\)', next_tag.text.strip()):
                            '''(h)(1)
                                  (2)
                               (i)(1)(i)
                                      (ii)
                            '''
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                        elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                            if alphabet == 'i' and re.search(r'^\(ii\)|^\(B\)',
                                                             next_tag.find_next_sibling().text.strip()):
                                continue
                            elif ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                        elif next_tag.name == "h4" or next_tag.name == "h3" or next_tag.name == "h5":
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            ol_count = 1
                    elif re.search(fr'^\({inner_num}\)', tag.text.strip()):
                        if re.search(fr'^\({inner_num}\) \({inner_roman}\)', tag.text.strip()):
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({inner_num}\) \({inner_roman}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_inner_roman)
                            tag['class'] = "inner_roman"
                            li_tag = self.soup.new_tag("li")
                            if ol_tag_for_caps_alphabet.li:
                                id_of_last_li = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].attrs[
                                    'id']
                                li_tag['id'] = f"{id_of_last_li}{inner_num}"
                                tag.attrs[
                                    'id'] = f'{ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].attrs["id"]}{inner_num}-{inner_roman}'
                            elif ol_tag_for_inner_alphabet.li:
                                id_of_last_li = ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].attrs['id']
                                li_tag['id'] = f"{id_of_last_li}{inner_num}"
                                tag.attrs[
                                    'id'] = f'{ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].attrs["id"]}{inner_num}-{inner_roman}'
                            elif ol_tag_for_number.li:
                                id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                                li_tag['id'] = f"{id_of_last_li}{inner_num}"
                                tag.attrs[
                                    'id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{inner_num}-{inner_roman}"

                            li_tag['class'] = "inner_num"
                            li_tag.append(ol_tag_for_inner_roman)
                            inner_roman = roman.fromRoman(inner_roman.upper())
                            inner_roman += 1
                            inner_roman = roman.toRoman(inner_roman).lower()
                            ol_tag_for_inner_number.append(li_tag)
                            inner_num += 1
                        else:
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({inner_num}\)', '', tag.text.strip())
                            if ol_tag_for_inner_roman.li:
                                id_of_last_li = ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].attrs['id']
                            elif ol_tag_for_caps_alphabet.li:
                                id_of_last_li = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].attrs['id']

                            elif ol_tag_for_roman.li:
                                id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                            elif ol_tag_for_inner_alphabet.li:
                                id_of_last_li = ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].attrs['id']
                            elif ol_tag_for_number.li:
                                id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{inner_num}"
                            tag['class'] = "inner_num"
                            ol_tag_for_inner_number.append(tag)
                            inner_num += 1
                            while next_tag.name != "h4" and next_tag.name != "h3" and not re.search(
                                    '^ARTICLE [IVXCL]+', next_tag.text.strip(),
                                    re.IGNORECASE) and (re.search(r"^“?[a-z A-Z]+|^\([a-z]+\)|^\((ix|iv|v?i{0,3})\)",
                                                                  next_tag.text.strip()) or (
                                                                next_tag.next_element and next_tag.next_element.name == "br")):
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search(fr'^{inner_alphabet}\.|^{caps_alpha}{caps_alpha}?\.',
                                               next_tag.text.strip()):
                                    break
                                elif re.search("^“?[a-z A-Z]+", next_tag.text.strip()):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                elif re.search(r'^\([a-z]+\)', next_tag.text.strip()):
                                    alphabet_id = re.search(r'^\((?P<alphabet_id>([a-z]+))\)', next_tag.text.strip()).group('alphabet_id')
                                    if alphabet_id[0] != alphabet and alphabet_id[0] != inner_alphabet and alphabet_id != roman_number and alphabet_id != inner_roman:
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                            count_of_p_tag = 1
                            if re.search(fr'^\({roman_number}\)',
                                         next_tag.text.strip()) and roman_number != "i":
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type='A')
                                    caps_alpha = 'A'
                                else:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_inner_number)
                                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                                    inner_num = 1
                            elif re.search(fr'^\({inner_roman}\)', next_tag.text.strip()) and inner_roman != "i":
                                ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].append(
                                    ol_tag_for_inner_number)
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                            elif re.search(fr'^\({caps_alpha}{caps_alpha}?\)', next_tag.text.strip()):
                                if ol_tag_for_caps_roman.li:
                                    ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_caps_roman)
                                    ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                                    caps_roman = "I"
                                elif ol_tag_for_inner_roman.li:
                                    ol_tag_for_inner_roman.find_all("li", class_="inner_roman")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_roman)
                                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                    inner_roman = "i"
                                else:

                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                            elif re.search(fr'^\({caps_roman}\)', next_tag.text.strip()):
                                ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(
                                    ol_tag_for_inner_number)
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                            elif re.search(fr'^\({inner_alphabet}\)|^{inner_alphabet}\.',
                                           next_tag.text.strip()) and inner_alphabet != "a":
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_inner_number)
                                    ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                        ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                elif ol_tag_for_inner_alphabet.li:
                                    ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                            elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()) and alphabet != 'a':
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_inner_number)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_number)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1

                            if next_tag.name == "h4" or next_tag.name == "h3":
                                if ol_tag_for_caps_alphabet.li:
                                    ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1].append(
                                        ol_tag_for_inner_number)
                                    if ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_caps_alphabet)
                                        if ol_tag_for_alphabet.li:
                                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                                ol_tag_for_number)
                                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                            alphabet = "a"
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                    caps_alpha = "A"
                                elif ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                        ol_tag_for_inner_number)
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_number)
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = "a"
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_num = 1
                                ol_count = 1

            if tag.name in ["h2", "h3", "h4"]:
                ol_count = 1
            # if tag.name == "p" and re.search(r'^\([a-zA-Z0-9]+\)', tag.text.strip()):
            #     print(tag)
        # for tag in self.soup.find_all("p"):
            # class_name = tag['class'][0]
            # if tag.name == "p" and (class_name == self.tag_type_dict['history'] or class_name == self.tag_type_dict['ol_of_i'] or class_name == self.tag_type_dict['head4'] )and re.search(r'^[A-Za-z0-9]\.|^“?\([A-Z a-z0-9]+\)|^\([\w ]{4,}|^\. \. \.|^\[[A-Z a-z]+|^“?(\*\*)?[a-z A-Z]+|^\*“?[A-Za-z ]+|^_______________|^“?[a-z A-Z]+', tag.text.strip()) and not tag.has_attr('id') and not re.search('(Mass\.|U\.S\.|^Conn\.|N\.E\.|P.L. \d+|G\.\s?L\.|C\.I\.F\.|^[a-zA-Z0-9 ]+|R\.I\.|P\.S\.|G\.S\.|B\. Mitchell|Y\.M\.C\.A\.|A\.L\.R\.)', tag.text.strip()):
            #     print(tag)
        # l=[]
        # for tag in self.soup.main.find_all():
        #     if tag.has_attr('id') and tag['id'] not in l:
        #         l.append((tag['id']).lower())
        #     elif tag.has_attr('id') and tag['id'] in l:
        #         print('duplicate:{0}', tag['id'])
        # print(l)
        #     if tag.get('class') == [self.tag_type_dict["head4"]] and not tag.has_attr('id')and tag.b and not re.search(
        #             '^Mass\.|^Conn\.|P\.L\.|"^\([A-Za-z0-9]\)', tag.text.strip()):
        #         print(tag)
        for tag in self.soup.main.find_all(["li","p"]):
            if (tag.name == "li" and tag['class'] != "note") or (tag.name == "p" and tag['class'] == "text") :
                del tag["class"]

        print('ol tags added')

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_Notes_to_decision_analysis_nav_tag_con()
        else:
            super(RIParseHtml, self).create_Notes_to_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")

    def replace_tags_constitution(self):
        self.regex_pattern_obj = CustomisedRegexRI()
        super(RIParseHtml, self).replace_tags_constitution()
        note_to_decision_list: list = []
        note_to_decision_id: list = []
        h4_count = 1
        count = 1
        h5count = 1
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^NOTES TO DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict['ol_of_i']] and not re.search('^Click to view', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            note_to_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict['head4']] and tag.b and not re.search(
                                r'Collateral References\.', tag.b.text):
                            if tag.text.strip() in note_to_decision_list:
                                if re.search(r'^—\s*\w+', tag.text.strip()):
                                    tag.name = "h5"
                                    inner_case_tag = tag
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    p_tag_inner_id = f'{case_tag.get("id")}-{tag_text}'
                                    if p_tag_inner_id in note_to_decision_id:
                                        tag["id"] = f'{p_tag_inner_id}.{count:02}'
                                        count += 1
                                    else:
                                        tag["id"] = p_tag_inner_id
                                        count = 1
                                    note_to_decision_id.append(p_tag_inner_id)
                                elif re.search(r'^— —\s*\w+', tag.text.strip()):
                                    tag.name = "h5"
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    p_tag_inner1_id = f'{inner_case_tag.get("id")}-{tag_text}'
                                    if p_tag_inner1_id in note_to_decision_id:
                                        tag["id"] = f'{p_tag_inner1_id}.{count:02}'
                                        count += 1
                                    else:
                                        tag["id"] = p_tag_inner1_id
                                        count = 1
                                    note_to_decision_id.append(p_tag_inner1_id)
                                else:
                                    tag.name = "h5"
                                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                    p_tag_id = f'{tag.find_previous(["h3","h2"]).get("id")}-notetodecision-{tag_text}'
                                    if p_tag_id in note_to_decision_id:
                                        tag["id"] = f'{p_tag_id}.{h5count:02}'
                                        h5count += 1
                                    else:
                                        tag["id"] = f'{p_tag_id}'
                                        h5count = 1
                                    note_to_decision_id.append(p_tag_id)
                                    case_tag = tag
                            else:
                                tag.name = "h5"
                                tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                p_tag_id = f'{tag.find_previous(["h3","h2"]).get("id")}-notetodecision-{tag_text}'
                                if p_tag_id in note_to_decision_id:
                                    tag["id"] = f'{p_tag_id}.{h5count:02}'
                                    h5count += 1
                                else:
                                    tag["id"] = f'{p_tag_id}'
                                    h5count = 1
                                note_to_decision_id.append(p_tag_id)
                                case_tag = tag
                        elif tag.name in ["h2", "h3", "h4"]:
                            break
                if p_tag.text.strip() in self.h4_head:
                    header4_tag_text = re.sub(r'[\W.]+', '', p_tag.text.strip()).lower()
                    h4_tag_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'

                    if h4_tag_id in self.h4_cur_id_list:
                        p_tag['id'] = f'{h4_tag_id}.{h4_count}'
                        h4_count += 1
                    else:
                        p_tag['id'] = f'{h4_tag_id}'

                    self.h4_cur_id_list.append(h4_tag_id)

            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["ul"]]:
                    p_tag.name = "li"
                    p_tag.wrap(self.ul_tag)
                elif p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    if re.search(r"^History of Section\.", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', new_tag.text.strip()).lower()
                        new_tag.attrs['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"
                elif p_tag.name == "p" and p_tag.get("class") == [self.tag_type_dict["head2"]]:
                    if re.search('^Rhode Island Constitution', p_tag.text.strip()):
                        p_tag.name = "h3"
                        match = re.search('^Rhode Island Constitution', p_tag.text.strip()).group()
                        r_id = re.sub("[^A-Za-z0-9]", "", match)
                        header_tag_id = f'{p_tag.find_previous_sibling("h2").attrs["id"]}-{r_id}'
                        if header_tag_id in self.h2_rep_id:
                            p_tag["id"] = f'{header_tag_id}.{self.h2_id_count:02}'
                            self.h2_id_count += 1
                        else:
                            p_tag["id"] = f'{header_tag_id}'
                            self.h2_id_count = 1
                        p_tag["class"] = "oneh2"
                        self.h2_rep_id.append(p_tag['id'])
            elif p_tag.name == "h2" and p_tag.get("class") == "oneh2":
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            elif p_tag.name == "h3" and self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()):
                chap_no = self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()).group('id')
                p_tag['id'] = f'{p_tag.find_previous(["h2","h3"],["oneh2", "gen", "amd"]).get("id")}-s{chap_no.zfill(2)}'
