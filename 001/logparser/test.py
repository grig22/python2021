import unittest
import datetime
from log_analyzer import split_filenames, parse_log, calculate_statistics


class TruthTest(unittest.TestCase):

    def testSplit(self):
        names = ['nginx-access-ui.log-20170630.gz']
        expected = ('nginx-access-ui.log-20170630.gz',
                    datetime.date.fromisoformat(f'2017-06-30'),
                    'gz')
        actual = list(split_filenames(names=names))[0]
        self.assertEqual(expected, actual)

    def testParse(self):
        collector = dict()
        text = ['1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/24987703 HTTP/1.1" 200 883 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752753" "dc7161be3" 0.726']
        parse_log(collector=collector, text=text, max_err_perc=0)
        self.assertEqual(collector['/api/v2/banner/24987703'][0], '0.726')

    def testStatistics(self):
        url = 'https://www.dea.gov/'
        tim = 0.24
        collector = {url: [tim]}
        calculate_statistics(collector=collector, report_size=1)
        self.assertEqual(collector[url]['url'], url)
        self.assertEqual(collector[url]['count'], 1)
        self.assertAlmostEqual(collector[url]['time_avg'], tim, places=3)
        self.assertAlmostEqual(collector[url]['time_max'], tim, places=3)
        self.assertAlmostEqual(collector[url]['time_sum'], tim, places=3)
        self.assertAlmostEqual(collector[url]['time_med'], tim, places=3)
        self.assertAlmostEqual(collector[url]['time_perc'], 100, places=3)
        self.assertAlmostEqual(collector[url]['count_perc'], 100, places=3)


if __name__ == '__main__':
    unittest.main()