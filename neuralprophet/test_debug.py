import pandas as pd
import matplotlib.pyplot as plt
import logging

from neuralprophet.neural_prophet import NeuralProphet
from neuralprophet import set_global_log_level

log = logging.getLogger(__name__)


def test_names(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    m = NeuralProphet()
    m._validate_column_name("hello_friend")


def test_train_eval_test(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    m = NeuralProphet(
        n_lags=14,
        n_forecasts=7,
        ar_sparsity=0.1,
    )
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    df_train, df_test = m.split_df(df, valid_p=0.1, inputs_overbleed=True)

    metrics = m.fit(df_train, validate_each_epoch=True, valid_p=0.1)
    val_metrics = m.test(df_test)
    if log.level == "DEBUG":
        print("Metrics: train/eval")
        print(metrics.to_string(float_format=lambda x: "{:6.3f}".format(x)))
        print("Metrics: test")
        print(val_metrics.to_string(float_format=lambda x: "{:6.3f}".format(x)))


def test_trend(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_changepoints=100,
        trend_smoothness=2,
        # trend_threshold=False,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    m.fit(df)
    future = m.make_future_dataframe(df, future_periods=60, n_historic_predictions=len(df))
    forecast = m.predict(df=future)
    if log.level == "NOTSET":
        m.plot(forecast)
        m.plot_components(forecast)
        m.plot_parameters()
        plt.show()


def test_ar_net(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=14,
        n_lags=28,
        ar_sparsity=0.01,
        # num_hidden_layers=0,
        num_hidden_layers=2,
        # d_hidden=64,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    m.highlight_nth_step_ahead_of_each_forecast(m.n_forecasts)
    m.fit(df, validate_each_epoch=True)
    future = m.make_future_dataframe(df, n_historic_predictions=len(df))
    forecast = m.predict(df=future)
    if log.level == "NOTSET":
        m.plot_last_forecast(forecast, include_previous_forecasts=3)
        m.plot(forecast)
        m.plot_components(forecast)
        m.plot_parameters()
        plt.show()


def test_seasons(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    # m = NeuralProphet(n_lags=60, n_changepoints=10, n_forecasts=30, verbose=True)
    m = NeuralProphet(
        # n_forecasts=1,
        # n_lags=1,
        # n_changepoints=5,
        # trend_smoothness=0,
        yearly_seasonality=8,
        weekly_seasonality=4,
        # daily_seasonality=False,
        # seasonality_mode='additive',
        seasonality_mode='multiplicative',
        # seasonality_reg=10,
    )
    m.fit(df, validate_each_epoch=True)
    future = m.make_future_dataframe(df, n_historic_predictions=len(df), future_periods=365)
    forecast = m.predict(df=future)

    if log.level == "DEBUG":
        print(sum(abs(m.model.season_params["yearly"].data.numpy())))
        print(sum(abs(m.model.season_params["weekly"].data.numpy())))
        print(m.model.season_params.items())
    if log.level == "NOTSET":
        m.plot(forecast)
        m.plot_components(forecast)
        m.plot_parameters()
        plt.show()


def test_lag_reg(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=3,
        n_lags=5,
        ar_sparsity=0.1,
        # num_hidden_layers=2,
        # d_hidden=64,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    if m.n_lags > 0:
        df['A'] = df['y'].rolling(7, min_periods=1).mean()
        df['B'] = df['y'].rolling(30, min_periods=1).mean()
        m = m.add_lagged_regressor(name='A')
        m = m.add_lagged_regressor(name='B', only_last_value=True)

        # m.highlight_nth_step_ahead_of_each_forecast(m.n_forecasts)
    m.fit(df, validate_each_epoch=True)
    future = m.make_future_dataframe(df, n_historic_predictions=365)
    forecast = m.predict(future)

    if log.level == "NOTSET":
        # print(forecast.to_string())
        m.plot_last_forecast(forecast, include_previous_forecasts=10)
        m.plot(forecast)
        m.plot_components(forecast, figsize=(10, 30))
        m.plot_parameters(figsize=(10,30))
        plt.show()


def test_events(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    playoffs = pd.DataFrame({
        'event': 'playoff',
        'ds': pd.to_datetime(['2008-01-13', '2009-01-03', '2010-01-16',
                              '2010-01-24', '2010-02-07', '2011-01-08',
                              '2013-01-12', '2014-01-12', '2014-01-19',
                              '2014-02-02', '2015-01-11', '2016-01-17',
                              '2016-01-24', '2016-02-07']),
    })
    superbowls = pd.DataFrame({
        'event': 'superbowl',
        'ds': pd.to_datetime(['2010-02-07', '2014-02-02', '2016-02-07']),
    })
    events_df = pd.concat((playoffs, superbowls))

    m = NeuralProphet(
        n_lags=5,
        n_forecasts=3,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    # set event windows
    m = m.add_events(["superbowl", "playoff"], lower_window=-1, upper_window=1, mode="multiplicative", regularization=0.5)

    # add the country specific holidays
    m = m.add_country_holidays("US", mode="additive", regularization=0.5)

    history_df = m.create_df_with_events(df, events_df)
    m.fit(history_df)

    # create the test data
    history_df = m.create_df_with_events(df.iloc[100: 500, :].reset_index(drop=True), events_df)
    future = m.make_future_dataframe(df=history_df, events_df=events_df, future_periods=20, n_historic_predictions=3)
    forecast = m.predict(df=future)
    if log.level == "DEBUG":
        print(m.model.event_params)
    if log.level == "NOTSET":
        m.plot_components(forecast, figsize=(10, 30))
        m.plot(forecast)
        m.plot_parameters(figsize=(10, 30))
        plt.show()


def test_future_reg(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=1,
        n_lags=0,
    )

    df['A'] = df['y'].rolling(7, min_periods=1).mean()
    df['B'] = df['y'].rolling(30, min_periods=1).mean()

    m = m.add_future_regressor(name='A', regularization=0.5)
    m = m.add_future_regressor(name='B', mode="multiplicative", regularization=0.3)

    m.fit(df)
    regressors_df = pd.DataFrame(data={'A': df['A'][:50], 'B': df['B'][:50]})
    future = m.make_future_dataframe(df=df, regressors_df=regressors_df, n_historic_predictions=10, future_periods=50)
    forecast = m.predict(df=future)

    if log.level == "NOTSET":
        # print(forecast.to_string())
        # m.plot_last_forecast(forecast, include_previous_forecasts=3)
        m.plot(forecast)
        m.plot_components(forecast, figsize=(10, 30))
        m.plot_parameters(figsize=(10, 30))
        plt.show()


def test_predict(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=3,
        n_lags=5,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    m.fit(df)
    future = m.make_future_dataframe(df, future_periods=None, n_historic_predictions=10)
    forecast = m.predict(future)
    if log.level == "NOTSET":
        m.plot_last_forecast(forecast, include_previous_forecasts=10)
        m.plot(forecast)
        m.plot_components(forecast)
        m.plot_parameters()
        plt.show()


def test_plot(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=7,
        n_lags=14,
        # yearly_seasonality=8,
        # weekly_seasonality=4,
        # daily_seasonality=False,
    )
    m.fit(df)
    m.highlight_nth_step_ahead_of_each_forecast(7)
    future = m.make_future_dataframe(df, n_historic_predictions=10)
    forecast = m.predict(future)
    # print(future.to_string())
    # print(forecast.to_string())
    # m.plot_last_forecast(forecast)
    m.plot(forecast)
    m.plot_components(forecast)
    m.plot_parameters()
    if log.level == "NOTSET":
        plt.show()


def test_logger(log_level=None):
    if log_level is not None:
        set_global_log_level(log_level)
    # test existing test cases
    # test_all(log_level="DEBUG")

    # test the set_log_level function
    df = pd.read_csv('../example_data/example_wp_log_peyton_manning.csv')
    m = NeuralProphet(
        n_forecasts=3,
        n_lags=5,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    m.fit(df, validate_each_epoch=True)

    m.set_log_level(log_level="WARNING")
    future = m.make_future_dataframe(df, future_periods=None, n_historic_predictions=10)
    forecast = m.predict(future)


def test_all(log_level=None):
    """
    Note: log_level 'NOTSET' shows plots.
    """
    test_names(log_level)
    test_train_eval_test(log_level)
    test_trend(log_level)
    test_ar_net(log_level)
    test_seasons(log_level)
    test_lag_reg(log_level)
    test_events(log_level)
    test_predict(log_level)
    test_logger(log_level)


if __name__ == '__main__':
    """
    just used for debugging purposes. 
    should implement proper tests at some point in the future.
    (some test methods might already be deprecated)
    """
    # test_all("DEBUG")
    # test_names("NOTSET")
    # test_train_eval_test("NOTSET")
    # test_trend("NOTSET")
    # test_ar_net("NOTSET")
    # test_seasons("NOTSET")
    # test_lag_reg("NOTSET")
    # test_future_reg("NOTSET")
    # test_events("NOTSET")
    # test_predict("NOTSET")
    # test_plot("NOTSET")
    test_logger("NOTSET")
