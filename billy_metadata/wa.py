
metadata = dict(
    name='Washington',
    abbreviation='wa',
    capitol_timezone='America/Los_Angeles',
    legislature_name='Washington State Legislature',
    legislature_url='http://www.leg.wa.gov/',
    chambers={
        'upper': {'name': 'Senate', 'title': 'Senator'},
        'lower': {'name': 'House', 'title': 'Representative'},
    },
    terms=[
        {'name': '2009-2010', 'start_year': 2009, 'end_year': 2010,
         'sessions': ['2009-2010']},
        {'name': '2011-2012', 'start_year': 2011, 'end_year': 2012,
         'sessions': ['2011-2012']},
        {'name': '2013-2014', 'start_year': 2013, 'end_year': 2014,
         'sessions': ['2013-2014']},
        {'name': '2015-2016', 'start_year': 2015, 'end_year': 2016,
         'sessions': ['2015-2016']},
        {'name': '2017-2018', 'start_year': 2017, 'end_year': 2018,
         'sessions': ['2017-2018']},
        ],
    session_details={
        '2009-2010': {'display_name': '2009-2010 Regular Session',
                      '_scraped_name': '2009-10',
                      },
        '2011-2012': {'display_name': '2011-2012 Regular Session',
                      '_scraped_name': '2011-12',
                      },
        '2013-2014': {'display_name': '2013-2014 Regular Session',
                      '_scraped_name': '2013-14',
                      },
        '2015-2016': {'display_name': '2015-2016 Regular Session',
                      '_scraped_name': '2015-16',
                      },
        '2017-2018': {'display_name': '2017-2018 Regular Session',
                      '_scraped_name': '2017-18',
                      },
    },
    feature_flags=['events', 'subjects', 'capitol_maps', 'influenceexplorer'],
    capitol_maps=[
        {"name": "Floor 1",
         "url": 'http://static.openstates.org/capmaps/wa/f1.gif'
         },
        {"name": "Floor 2",
         "url": 'http://static.openstates.org/capmaps/wa/f2.gif'
         },
        {"name": "Floor 3",
         "url": 'http://static.openstates.org/capmaps/wa/f3.gif'
         },
        {"name": "Floor 4",
         "url": 'http://static.openstates.org/capmaps/wa/f4.gif'
         },
    ],
    _ignored_scraped_sessions=['2007-08', '2005-06', '2003-04', '2001-02',
                               '1999-00', '1997-98', '1995-96', '1993-94',
                               '1991-92', '1989-90', '1987-88', '1985-86'],
)
