import re
import datetime

import lxml.html

from pupa.scrape import Scraper, Bill, VoteEvent


class AKBillScraper(Scraper):
    bill_list_page = None

    _fiscal_dept_mapping = {
        'ADM': 'Administration',
        'CED': 'Commerce, Community & Economic Development',
        'COR': 'Corrections',
        'CRT': 'Court System',
        'EED': 'Education and Early Development',
        'DEC': 'Environmental Conservation ',
        'DFG': 'Fish and Game',
        'GOV': "Governor's Office",
        'DHS': 'Health and Social Services',
        'LWF': 'Labor and Workforce Development',
        'LAW': 'Law',
        'LEG': 'Legislative Agency',
        'MVA': "Military and Veterans' Affairs",
        'DNR': 'Natural Resources',
        'DPS': 'Public Safety',
        'REV': 'Revenue',
        'DOT': 'Transportation and Public Facilities',
        'UA': 'University of Alaska',
        'ALL': 'All Departments'}

    _comm_vote_type = {
        'DP': 'Do Pass',
        'DNP': 'Do Not Pass',
        'NR': 'No Recommendation',
        'AM': 'Amend'}

    _comm_mapping = {
        'AET': 'Arctic Policy, Economic Development, & Tourism',
        'CRA': 'Community & Regional Affairs',
        'EDC': 'Education',
        'FIN': 'Finance',
        'HSS': 'Health & Social Services',
        'JUD': 'Judiciary',
        'L&C': 'Labor & Commerce',
        'RES': 'Resources',
        'RLS': 'Rules',
        'STA': 'State Affairs',
        'TRA': 'Transportation',
        'EDT': 'Economic Development, Trade & Tourism',
        'NRG': 'Energy',
        'FSH': 'Fisheries',
        'MLV': 'Military & Veterans',
        'WTR': 'World Trade',
        'ARR': 'Administrative Regulation Review',
        'ASC': 'Armed Services Committee',
        'BUD': 'Legislative Budget & Audit',
        'ECR': 'Higher Education/Career Readiness Task Force',
        'EFF': 'Education Fuding District Cost Factor Committee',
        'ETH': 'Select Committee on Legislative Ethics',
        'LEC': 'Legislative Council',
        'ARC': 'Special Committee on the Arctic',
        'EDA': 'Economic Development, Trade, Tourism & Arctic Policy',
        'ENE': 'Energy',
    }

    _comm_re = re.compile(r'^(%s)\s' % '|'.join(_comm_mapping.keys()))
    _current_comm = None

    def scrape(self, chamber=None, session=None):
        if session is None:
            session = self.latest_session()
            self.info('no session specified, using %s', session)

        chambers = [chamber] if chamber is not None else ['upper', 'lower']
        for chamber in chambers:
            yield from self.scrape_chamber(chamber, session)

    def scrape_chamber(self, chamber, session):
        if chamber == 'upper':
            bill_abbrs = ('SB', 'SR', 'SCR', 'SJR')
        elif chamber == 'lower':
            bill_abbrs = ('HB', 'HR', 'HCR', 'HJR')
        bill_types = {'B': 'bill', 'R': 'resolution', 'JR': 'joint resolution',
                      'CR': 'concurrent resolution'}

        if self.bill_list_page is None:
            # putting H1 -> H999 returns all the bills, even senate
            bill_list_url = 'https://www.akleg.gov/basis/Bill/Range/{}?session=&billH1=1&bill2=H9999'.format(session)
            page = lxml.html.fromstring(self.get(bill_list_url).text)
            page.make_links_absolute('https://www.akleg.gov/')
            self.bill_list_page = page

        if chamber == 'upper':
            bill_type_xpath = '//div[contains(@class, "content-page")]/div/table/tr[contains(@class, "Senate")]/td[1]/nobr/a/@href'
        elif chamber == 'lower':
            bill_type_xpath = '//div[contains(@class, "content-page")]/div/table/tr[contains(@class, "House")]/td[1]/nobr/a/@href'

        for bill_link in self.bill_list_page.xpath(bill_type_xpath):
            yield from self.scrape_bill(chamber, session, bill_link)

    def classify_bill(self, bill_id):
        bill_types = {'B': 'bill', 'R': 'resolution', 'JR': 'joint resolution',
                      'CR': 'concurrent resolution'}
        for abbr in bill_types:
            if abbr in bill_id:
                return bill_types[abbr]
        else:
            raise AssertionError("Could not categorize bill ID")

    def extract_ak_field(self, page, field):
        # AK bill page has the same structure for lots of fields
        # <li><span>Field</span><strong>Content</strong>
        # Careful, how they appear styled and the page source are different
        return page.xpath('//li[./span[text()="{}"]]/strong/text()'.format(field))[0]

    def scrape_bill(self, chamber, session, bill_link):
        page = lxml.html.fromstring(self.get(bill_link).text)
        page.make_links_absolute('https://www.akleg.gov')

        bill_id = self.extract_ak_field(page, 'Bill ').replace('   ', ' ')
        short_title = self.extract_ak_field(page, 'Short Title ')
        long_title = self.extract_ak_field(page, 'Title')

        sponsors = self.extract_ak_field(page, 'Sponsor(S) ')
        classification = self.classify_bill(bill_id)

        bill = Bill(
            bill_id,
            title=short_title,
            chamber=chamber,
            classification=classification,
            legislative_session=session,
        )
        bill.add_source(bill_link)

        print(sponsors)

        senate_sponsors = re.match(r'SENATOR[\(S\)]*\s*(?P<names>.*)\<br\>').group('names')
        house_sponsors = re.match(r'REPRESENTATIVE[\(S\)]*\s*(?P<names>.*)\<br\>').group('names')
        house_com_regex = r'HOUSE*\s*(?P<names>.*)\<br\>'
        senate_com_regex = r'SENATE*\s*(?P<names>.*)\<br\>'

        senate_sponsors = ','.split(senate_sponsors.strip())

        for sponsor in senate_sponsors:
            if sponsor.isupper():
                bill.add_sponsorship(
                    sponsor,
                    entity_type='person',
                    classification='primary',
                    primary=True,
                )
            else:
                bill.add_sponsorship(
                    sponsor,
                    entity_type='person',
                    classification='cosponsor',
                    primary=False,
                )

        for sponsor in house_sponsors:
            if sponsor.isupper():
                bill.add_sponsorship(
                    sponsor,
                    entity_type='person',
                    classification='primary',
                    primary=True,
                )
            else:
                bill.add_sponsorship(
                    sponsor,
                    entity_type='person',
                    classification='cosponsor',
                    primary=False,
                )

        # # Get actions from second myth table
        # self._current_comm = None
        # act_rows = doc.xpath('(//table[@class="myth"])[2]//tr')[1:]
        # for row in act_rows:
        #     date, journal, raw_chamber, action = row.xpath('td')

        #     act_date = datetime.datetime.strptime(date.text_content().strip(),
        #                                         '%m/%d/%y')
        #     raw_chamber = raw_chamber.text_content().strip()
        #     action = action.text_content().strip()

        #     if raw_chamber == "(H)":
        #         act_chamber = "lower"
        #     elif raw_chamber == "(S)":
        #         act_chamber = "upper"

        #     if re.match(r"\w+ Y(\d+)", action):
        #         vote_href = journal.xpath('.//a/@href')
        #         if vote_href:
        #             yield from self.parse_vote(bill, action, act_chamber, act_date,
        #                                     vote_href[0])

        #     action, atype = self.clean_action(action)

        #     match = re.match(r'^Prefile released (\d+/\d+/\d+)$', action)
        #     if match:
        #         action = 'Prefile released'
        #         act_date = datetime.datetime.strptime(match.group(1), '%m/%d/%y')

        #     bill.add_action(
        #         action, chamber=act_chamber, date=act_date.strftime('%Y-%m-%d'),
        #         classification=atype)

        # # Get subjects
        # for subj in doc.xpath('//a[contains(@href, "subject")]/text()'):
        #     bill.add_subject(subj.strip())

        # # Get versions
        # text_list_url = (
        #     "http://www.legis.state.ak.us/"
        #     "basis/get_fulltext.asp?session=%s&bill=%s"
        # ) % (session, bill_id)
        # bill.add_source(text_list_url)

        # text_doc = lxml.html.fromstring(self.get(text_list_url).text)
        # text_doc.make_links_absolute(text_list_url)
        # for link in text_doc.xpath('//a[contains(@href, "get_bill_text")]'):
        #     name = link.xpath('../preceding-sibling::td/text()')[0].strip()
        #     text_url = link.get('href')
        #     bill.add_version_link(name, text_url, media_type="text/html")

        # # Get documents
        # doc_list_url = (
        #     "http://www.legis.state.ak.us/"
        #     "basis/get_documents.asp?session=%s&bill=%s"
        # ) % (session, bill_id)
        # doc_list = lxml.html.fromstring(self.get(doc_list_url).text)
        # doc_list.make_links_absolute(doc_list_url)
        # bill.add_source(doc_list_url)
        # for href in doc_list.xpath('//a[contains(@href, "get_documents")][@onclick]'):
        #     h_name = href.text_content()
        #     h_href = href.attrib['href']
        #     if h_name.strip():
        #         bill.add_document_link(h_name, h_href)

        yield bill

    def parse_sponsors(self, bill, sponsor_str):

        regexes = [
            # senators
            ('S', r'SENATOR[\(S\)]*\s*(?P<names>.*)\<br\>'),
            ('H', r'REPRESENTATIVE[\(S\)]*\s*(?P<names>.*)\<br\>'),
        ]

        com_regexes = [
            ('S', r'SENATE*\s*(?P<names>.*)\<br\>'),
            ('H', r'HOUSE*\s*(?P<names>.*)\<br\>')
        ]

        for chamber_code, regex in regexes:
            sponsors = re.match(regex, sponsor_str).group('names')
            sponsors = ','.split(sponsors)

            for sponsor in sponsors:
                sponsor_name = '{} ({})'.format(sponsor_name.strip(), chamber_code)
                if sponsor.isupper(): # primary in uppercase
                    bill.add_sponsorship(
                        sponsor,
                        entity_type='person',
                        classification='primary',
                        primary=True,
                    )
                else:
                    bill.add_sponsorship(
                        sponsor,
                        entity_type='person',
                        classification='cosponsor',
                        primary=False,
                    )

    def parse_vote(self, bill, action, act_chamber, act_date, url):
        re_vote_text = re.compile(r'The question (?:being|to be reconsidered):\s*"(.*?\?)"', re.S)
        re_header = re.compile(r'\d{2}-\d{2}-\d{4}\s{10,}\w{,20} Journal\s{10,}\d{,6}\s{,4}')

        html = self.get(url).text
        doc = lxml.html.fromstring(html)

        if len(doc.xpath('//pre')) < 2:
            return

        # Find all chunks of text representing voting reports.
        votes_text = doc.xpath('//pre')[1].text_content()
        votes_text = re_vote_text.split(votes_text)
        votes_data = zip(votes_text[1::2], votes_text[2::2])

        iVoteOnPage = 0

        # Process each.
        for motion, text in votes_data:

            iVoteOnPage += 1
            yes = no = other = 0

            tally = re.findall(r'\b([YNEA])[A-Z]+:\s{,3}(\d{,3})', text)
            for vtype, vcount in tally:
                vcount = int(vcount) if vcount != '-' else 0
                if vtype == 'Y':
                    yes = vcount
                elif vtype == 'N':
                    no = vcount
                else:
                    other += vcount

            vote = VoteEvent(
                bill=bill,
                start_date=act_date.strftime('%Y-%m-%d'),
                chamber=act_chamber,
                motion_text=motion,
                result='pass' if yes > no else 'fail',
                classification='passage',
            )
            vote.set_count('yes', yes)
            vote.set_count('no', no)
            vote.set_count('other', other)

            vote.pupa_id = (url + ' ' + str(iVoteOnPage)) if iVoteOnPage > 1 else url

            # In lengthy documents, the "header" can be repeated in the middle
            # of content. This regex gets rid of it.
            vote_lines = re_header.sub('', text)
            vote_lines = vote_lines.split('\r\n')

            vote_type = None
            for vote_list in vote_lines:
                if vote_list.startswith('Yeas: '):
                    vote_list, vote_type = vote_list[6:], 'yes'
                elif vote_list.startswith('Nays: '):
                    vote_list, vote_type = vote_list[6:], 'no'
                elif vote_list.startswith('Excused: '):
                    vote_list, vote_type = vote_list[9:], 'other'
                elif vote_list.startswith('Absent: '):
                    vote_list, vote_type = vote_list[9:], 'other'
                elif vote_list.strip() == '':
                    vote_type = None
                if vote_type:
                    for name in vote_list.split(','):
                        name = name.strip()
                        if name:
                            vote.vote(vote_type, name)

            vote.add_source(url)

            yield vote

    def clean_action(self, action):
        # Clean up some acronyms
        match = re.match(r'^FN(\d+): (ZERO|INDETERMINATE)?\((\w+)\)', action)
        if match:
            num = match.group(1)

            if match.group(2) == 'ZERO':
                impact = 'No fiscal impact'
            elif match.group(2) == 'INDETERMINATE':
                impact = 'Indeterminate fiscal impact'
            else:
                impact = ''

            dept = match.group(3)
            dept = self._fiscal_dept_mapping.get(dept, dept)

            action = "Fiscal Note %s: %s (%s)" % (num, impact, dept)

        match = self._comm_re.match(action)
        if match:
            self._current_comm = match.group(1)

        match = re.match(r'^(DP|DNP|NR|AM):\s(.*)$', action)
        if match:
            vtype = self._comm_vote_type[match.group(1)]

            action = "%s %s: %s" % (self._current_comm, vtype,
                                    match.group(2))

        match = re.match(r'^COSPONSOR\(S\): (.*)$', action)
        if match:
            action = "Cosponsors added: %s" % match.group(1)

        match = re.match('^([A-Z]{3,3}), ([A-Z]{3,3})$', action)
        if match:
            action = "REFERRED TO %s and %s" % (
                self._comm_mapping[match.group(1)],
                self._comm_mapping[match.group(2)])

        match = re.match('^([A-Z]{3,3})$', action)
        if match:
            action = 'REFERRED TO %s' % self._comm_mapping[action]

        match = re.match('^REFERRED TO (.*)$', action)
        if match:
            comms = match.group(1).title().replace(' And ', ' and ')
            action = "REFERRED TO %s" % comms

        action = re.sub(r'\s+', ' ', action)

        action = action.replace('PREFILE RELEASED', 'Prefile released')

        atype = []
        if 'READ THE FIRST TIME' in action:
            atype.append('introduction')
            atype.append('reading-1')
            action = action.replace('READ THE FIRST TIME',
                                    'Read the first time')
        if 'READ THE SECOND TIME' in action:
            atype.append('reading-2')
            action = action.replace('READ THE SECOND TIME',
                                    'Read the second time')
        if 'READ THE THIRD TIME' in action:
            atype.append('reading-3')
            action = action.replace('READ THE THIRD TIME',
                                    'Read the third time')
        if 'TRANSMITTED TO GOVERNOR' in action:
            atype.append('executive-receipt')
            action = action.replace('TRANSMITTED TO GOVERNOR',
                                    'Transmitted to Governor')
        if 'SIGNED INTO LAW' in action:
            atype.append('executive-signature')
            action = action.replace('SIGNED INTO LAW', 'Signed into law')
        if 'Do Pass' in action:
            atype.append('committee-passage')
        if 'Do Not Pass' in action:
            atype.append('committee-failure')
        if action.startswith('PASSED'):
            atype.append('passage')
        if 'REFERRED TO' in action:
            atype.append('referral-committee')
            action = action.replace('REFERRED TO', 'Referred to')
        if 'Prefile released' in action:
            atype.append('filing')

        return action, atype
