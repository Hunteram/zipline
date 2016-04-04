#
# Copyright 2016 Quantopian, Inc.
#

from bcolz import ctable
from numpy import uint32, int64
from pandas import DataFrame, Timestamp
from zipline.data.us_equity_pricing import (
    BcolzDailyBarReader,
    BcolzDailyBarWriter,
    OHLC,
)
from zipline.data.data_checks import (
    UnpairedDailyBars,
)


from zipline.testing.fixtures import (
    WithTempdir,
    WithTradingEnvironment,
    WithAssetFinder,
    ZiplineTestCase,
)


class BcolzDailyBarWriterFromFrames(BcolzDailyBarWriter):

    def __init__(self, frames):
        self.frames = frames

    def gen_tables(self, assets):
        """
        Read CSVs as DataFrames from our asset map.
        """
        for asset in assets:
            data = self.frames[asset]
            yield int(asset), ctable.fromdataframe(data)

    def to_uint32(self, array, colname):
        if colname in OHLC:
            return (array * 1000).astype(uint32)
        elif colname == 'volume':
            return array.astype(uint32)
        elif colname == 'day':
            array = array.astype('datetime64[ns]')
            nanos_per_second = (1000 * 1000 * 1000)
            return (array.view(int64) / nanos_per_second).astype(uint32)


class UnpairedDailyBarTestCase(WithTempdir,
                               WithTradingEnvironment,
                               WithAssetFinder,
                               ZiplineTestCase):

    TRADING_ENV_MIN_DATE = Timestamp("2016-03-01", tz="UTC")
    TRADING_ENV_MAX_DATE = Timestamp("2016-03-31", tz="UTC")

    @classmethod
    def init_class_fixtures(cls):
        super(UnpairedDailyBarTestCase, cls).init_class_fixtures()

        cls.path_a = cls.tempdir.makedir('a')
        cls.path_b = cls.tempdir.makedir('b')

        writer_a = BcolzDailyBarWriterFromFrames(cls.make_reader_a_data())
        cls.assets = cls.env.asset_finder.retrieve_all(
            cls.env.asset_finder.sids)
        writer_a.write(
            cls.path_a, cls.env.trading_days, cls.assets)
        writer_b = BcolzDailyBarWriterFromFrames(cls.make_reader_b_data())
        writer_b.write(
            cls.path_b, cls.env.trading_days, cls.assets)

        cls.reader_a = BcolzDailyBarReader(cls.path_a)
        cls.reader_b = BcolzDailyBarReader(cls.path_b)

    def init_instance_fixtures(self):
        super(UnpairedDailyBarTestCase, self).init_instance_fixtures()

        self.daily_bar_comparison = UnpairedDailyBars(
            self.env.trading_days,
            self.asset_finder,
            self.reader_a,
            self.reader_b,
            self.assets,
        )

    @classmethod
    def make_equities_info(cls):
        return DataFrame.from_dict({
            1: {
                "start_date": Timestamp("2016-03-01", tz="UTC"),
                "end_date": Timestamp("2016-03-31", tz="UTC"),
                "symbol": "EQUITY1",
            },
            2: {
                "start_date": Timestamp("2016-03-28", tz='UTC'),
                "end_date": Timestamp("2016-03-31", tz='UTC'),
                "symbol": "EQUITY2"
            },
        },
            orient='index')


class UnpairedDailyBarAllEqual(UnpairedDailyBarTestCase):

    @classmethod
    def make_reader_a_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close':  [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days
            }),
            2: DataFrame({
                'open': [205.1, 205.2, 205.3],
                'high': [210.1, 210.2, 210.3],
                'low': [200.1, 200.2, 200.3],
                'close': [206.1, 206.2, 206.3],
                'volume': [200000, 200001, 200002],
                'day': days,
            })
        }

    @classmethod
    def make_reader_b_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close': [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days,
            }),
            2: DataFrame({
                'open': [205.1, 205.2, 205.3],
                'high': [210.1, 210.2, 210.3],
                'low': [200.1, 200.2, 200.3],
                'close': [206.1, 206.2, 206.3],
                'volume': [200000, 200001, 200002],
                'day': days,
            })
        }

    def test_equal(self):
        expected = {}
        unpaired = self.daily_bar_comparison.unpaired(
            self.TRADING_ENV_MIN_DATE,
            self.TRADING_ENV_MAX_DATE,
        )
        self.assertEqual(expected, unpaired)


class UnpairedDailyBarMissingInB(UnpairedDailyBarTestCase):

    @classmethod
    def make_reader_a_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close':  [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days,
            }),
            2: DataFrame({
                'open': [205.1, 205.2, 205.3],
                'high': [210.1, 210.2, 210.3],
                'low': [200.1, 200.2, 200.3],
                'close': [206.1, 206.2, 206.3],
                'volume': [200000, 200001, 200002],
                'day': days,
            })
        }

    @classmethod
    def make_reader_b_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close': [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days,
            }),
            2: DataFrame({
                'open': [205.1, 0, 205.3],
                'high': [210.1, 0, 210.3],
                'low': [200.1, 0, 200.3],
                'close': [206.1, 0, 206.3],
                'volume': [200000, 0, 200002],
                'day': days,
            })
        }

    def test_missing_in_b(self):
        expected = {
            self.asset_finder.retrieve_asset(2):
            ([Timestamp('2016-03-29', tz='UTC')], [200001], [0])
        }
        unpaired = self.daily_bar_comparison.unpaired(
            self.TRADING_ENV_MIN_DATE,
            self.TRADING_ENV_MAX_DATE,
        )
        self.assertEqual(expected, unpaired)


class UnpairedDailyBarMissingInA(UnpairedDailyBarTestCase):

    @classmethod
    def make_reader_a_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close':  [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days,
            }),
            2: DataFrame({
                'open': [205.1, 0, 205.3],
                'high': [210.1, 0, 210.3],
                'low': [200.1, 0, 200.3],
                'close': [206.1, 0, 206.3],
                'volume': [200000, 0, 200002],
                'day': days,
            })
        }

    @classmethod
    def make_reader_b_data(cls):
        tds = cls.env.trading_days
        days = tds[tds.slice_indexer('2016-03-25', '2016-03-30')].asi8
        return {
            1: DataFrame({
                'open': [105.1, 105.2, 105.3],
                'high': [110.1, 110.2, 110.3],
                'low': [100.1, 100.2, 100.3],
                'close': [106.1, 106.2, 106.3],
                'volume': [100000, 100001, 100002],
                'day': days,
            }),
            2: DataFrame({
                'open': [205.1, 205.2, 205.3],
                'high': [210.1, 210.2, 210.3],
                'low': [200.1, 200.2, 200.3],
                'close': [206.1, 206.2, 206.3],
                'volume': [200000, 200001, 200002],
                'day': days,
            })
        }

    def test_missing_in_a(self):
        expected = {
            self.asset_finder.retrieve_asset(2):
            ([Timestamp('2016-03-29', tz='UTC')], [0], [200001])
        }
        unpaired = self.daily_bar_comparison.unpaired(
            self.TRADING_ENV_MIN_DATE,
            self.TRADING_ENV_MAX_DATE,
        )
        self.assertEqual(expected, unpaired)
