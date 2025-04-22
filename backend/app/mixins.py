import calendar
from collections import deque
import datetime
import itertools
from django import forms
import jpholiday
from django.utils import timezone



class BaseCalendarMixin:
    """カレンダー関連Mixinの、基底クラス"""
    first_weekday = 6  # 0は月曜から、1は火曜から。6なら日曜日からになります。お望みなら、継承したビューで指定してください。
    week_names = ['月', '火', '水', '木', '金', '土', '日']  # これは、月曜日から書くことを想定します。['Mon', 'Tue'...

    def setup_calendar(self):
        """内部カレンダーの設定処理

        calendar.Calendarクラスの機能を利用するため、インスタンス化します。
        Calendarクラスのmonthdatescalendarメソッドを利用していますが、デフォルトが月曜日からで、
        火曜日から表示したい(first_weekday=1)、といったケースに対応するためのセットアップ処理です。

        """
        self._calendar = calendar.Calendar(self.first_weekday)

    def get_week_names(self):
        """first_weekday(最初に表示される曜日)にあわせて、week_namesをシフトする"""
        week_names = deque(self.week_names)
        week_names.rotate(-self.first_weekday)  # リスト内の要素を右に1つずつ移動...なんてときは、dequeを使うと中々面白いです
        return week_names


class MonthCalendarMixin(BaseCalendarMixin):
    """月間カレンダーの機能を提供するMixin"""

    def get_previous_month(self, date):
        """前月を返す"""
        if date.month == 1:
            return date.replace(year=date.year-1, month=12, day=1)
        else:
            return date.replace(month=date.month-1, day=1)

    def get_next_month(self, date):
        """次月を返す"""
        if date.month == 12:
            return date.replace(year=date.year+1, month=1, day=1)
        else:
            return date.replace(month=date.month+1, day=1)

    def get_month_days(self, date):
        """その月の全ての日を返す"""
        return self._calendar.monthdatescalendar(date.year, date.month)

    def get_current_month(self):
        """現在の月を返す"""
        month = self.kwargs.get('month')
        year = self.kwargs.get('year')
        if month and year:
            month = datetime.date(year=int(year), month=int(month), day=1)
        else:
            month = datetime.date.today().replace(day=1)
        return month

    def get_month_calendar(self):
        """月間カレンダー情報の入った辞書を返す"""
        self.setup_calendar()
        current_month = self.get_current_month()
        calendar_data = {
            'now': datetime.date.today(),
            'month_days': self.get_month_days(current_month),
            'month_current': current_month,
            'month_previous': self.get_previous_month(current_month),
            'month_next': self.get_next_month(current_month),
            'month_prev_year': current_month.replace(year=current_month.year - 1),
            'month_next_year': current_month.replace(year=current_month.year + 1),
            'week_names': self.get_week_names(),
        }
        return calendar_data


class WeekCalendarMixin(BaseCalendarMixin):
    """週間カレンダーの機能を提供するMixin"""

    def get_week_days(self):
        """その週の日を全て返す"""
        month = self.kwargs.get('month')
        year = self.kwargs.get('year')
        day = self.kwargs.get('day')
        if month and year and day:
            date = datetime.date(year=int(year), month=int(month), day=int(day))
        else:
            date = datetime.date.today()

        for week in self._calendar.monthdatescalendar(date.year, date.month):
            if date in week:  # 週ごとに取り出され、中身は全てdatetime.date型。該当の日が含まれていれば、それが今回表示すべき週です
                return week
            
    def get_week_holidays(self, days):
        """
        指定された週(days: dateオブジェクトのリスト)に含まれる祝日を
        {日付: 祝日名} の辞書で返す
        """
        holidays_dict = {}
        if not days:
            return holidays_dict

        first_day = days[0]
        last_day = days[-1]

        # 週が月をまたぐ場合を考慮して、開始月と終了月の祝日を取得
        months_to_check = set([(first_day.year, first_day.month)])
        if first_day.month != last_day.month:
            months_to_check.add((last_day.year, last_day.month))

        all_holidays = {}
        for year, month in months_to_check:
            try:
                month_hols = jpholiday.month_holidays(year, month)
                for dt, name in month_hols:
                    all_holidays[dt] = name
            except ValueError:
                continue # 対応していない年などはスキップ

        # 取得した祝日から、該当週に含まれるものだけを抽出
        for day in days:
            if day in all_holidays:
                holidays_dict[day] = all_holidays[day]
        return holidays_dict

    def get_week_calendar(self):
        """週間カレンダー情報の入った辞書を返す"""
        self.setup_calendar()
        days = self.get_week_days()
        first = days[0]
        last = days[-1]
        calendar_data = {
            'now': datetime.date.today(),
            'week_days': days,
            'week_previous': first - datetime.timedelta(days=7),
            'week_next': first + datetime.timedelta(days=7),
            'week_names': self.get_week_names(),
            'week_first': first,
            'week_last': last,
            'month_current': first.replace(day=1),
        }
        
        calendar_data['week_holidays'] = self.get_week_holidays(days)
        return calendar_data


class WeekWithScheduleMixin(WeekCalendarMixin):
    """スケジュール付きの、週間カレンダーを提供するMixin"""

    date_field = 'start_datetime'

    def get_week_schedules(self, start, end, days):
        """それぞれの日とスケジュールを返す"""
        lookup = {
            # '例えば、date__range: (1日, 31日)'を動的に作る
            '{}__range'.format(self.date_field): (start, end)
        }
        # 例えば、Schedule.objects.filter(date__range=(1日, 31日)) になる
        queryset = self.model.objects.filter(**lookup).order_by(self.date_field)

        # {1日のdatetime: 1日のスケジュール全て, 2日のdatetime: 2日の全て...}のような辞書を作る
        day_schedules = {day: [] for day in days}
        for schedule in queryset:
            schedule_date = getattr(schedule, self.date_field)
            schedule_date = timezone.localtime(schedule_date).date()
            schedule_enddate = getattr(schedule, 'end_datetime')
            schedule_enddate = timezone.localtime(schedule_enddate).date()

            # スケジュールの開始日から終了日まで、全ての日にスケジュールを追加
            while schedule_date <= schedule_enddate:
                if schedule_date in day_schedules:
                    # スケジュールの開始日から終了日まで、全ての日にスケジュールを追加
                    day_schedules[schedule_date].append(schedule)
                schedule_date += datetime.timedelta(days=1)
        return day_schedules
    
    def get_week_holidays(self, days):
        """
        指定された週(days: dateオブジェクトのリスト)に含まれる祝日を
        {日付: 祝日名} の辞書で返す
        """
        holidays_dict = {}
        if not days:
            return holidays_dict

        first_day = days[0]
        last_day = days[-1]

        # 週が月をまたぐ場合を考慮して、開始月と終了月の祝日を取得
        months_to_check = set([(first_day.year, first_day.month)])
        if first_day.month != last_day.month:
            months_to_check.add((last_day.year, last_day.month))

        all_holidays = {}
        for year, month in months_to_check:
            try:
                month_hols = jpholiday.month_holidays(year, month)
                for dt, name in month_hols:
                    all_holidays[dt] = name
            except ValueError:
                continue # 対応していない年などはスキップ

        # 取得した祝日から、該当週に含まれるものだけを抽出
        for day in days:
            if day in all_holidays:
                holidays_dict[day] = all_holidays[day]

        return holidays_dict

    def get_week_calendar(self):
        calendar_context = super().get_week_calendar()
        week_days = calendar_context['week_days']
        calendar_context['week_day_schedules'] = self.get_week_schedules(
            calendar_context['week_first'],
            calendar_context['week_last'],
            week_days
        )
        # 祝日取得処理
        calendar_context['week_holidays'] = self.get_week_holidays(week_days)
        return calendar_context


class MonthWithScheduleMixin(MonthCalendarMixin):
    """スケジュール付きの、月間カレンダーを提供するMixin"""
    
    date_field = 'start_datetime'

    def get_month_schedules(self, start, end, days):
        """それぞれの日とスケジュールを返す"""
        lookup = {
            # '例えば、date__range: (1日, 31日)'を動的に作る
            '{}__range'.format(self.date_field): (start, end)
        }
        # 例えば、Schedule.objects.filter(date__range=(1日, 31日)) になる
        queryset = self.model.objects.filter(**lookup).order_by(self.date_field)

        # {1日のdatetime: 1日のスケジュール全て, 2日のdatetime: 2日の全て...}のような辞書を作る
        day_schedules = {day: [] for week in days for day in week}
        for schedule in queryset:
            schedule_date = getattr(schedule, self.date_field)
            schedule_date = timezone.localtime(schedule_date).date()
            schedule_enddate = getattr(schedule, 'end_datetime')
            schedule_enddate = timezone.localtime(schedule_enddate).date()

            while schedule_date <= schedule_enddate:
                if schedule_date in day_schedules:
                    day_schedules[schedule_date].append(schedule)

                schedule_date += datetime.timedelta(days=1)



        # day_schedules辞書を、周毎に分割する。[{1日: 1日のスケジュール...}, {8日: 8日のスケジュール...}, ...]
        # 7個ずつ取り出して分割しています。
        day_items = list(day_schedules.items())
        size = len(day_schedules)
        return [{key: day_schedules[key] for key in itertools.islice(day_schedules, i, i+7)} for i in range(0, size, 7)]
    
    def get_month_holidays(self, year, month):
        """指定された年月の祝日を {日付: 祝日名} の辞書で返す"""
        try:
            # jpholiday.month_holidays は (datetime.date, 祝日名) のタプルのリストを返す
            holidays_tuple = jpholiday.month_holidays(year, month)
            # 日付(dateオブジェクト)をキー、祝日名を値とする辞書に変換
            holidays_dict = {date: name for date, name in holidays_tuple}
            return holidays_dict
        except ValueError:
            return {}
    

    def get_month_calendar(self):
        calendar_context = super().get_month_calendar()
        month_days = calendar_context['month_days']
        # 空でないことを確認
        if not month_days or not month_days[0]:
            calendar_context['month_day_schedules'] = []
            calendar_context['month_holidays'] = {}
            return calendar_context

        month_first = month_days[0][0]
        month_last = month_days[-1][-1]

        # スケジュール取得
        calendar_context['month_day_schedules'] = self.get_month_schedules(
            month_first,
            month_last,
            month_days
        )

        # 祝日取得処理
        holidays_dict = {}
        date_cursor = month_first
        # 1日ずつ進めながら祝日を取得
        while date_cursor <= month_last:
            holidays_dict.update(self.get_month_holidays(date_cursor.year, date_cursor.month))
            date_cursor += datetime.timedelta(days=1)

            calendar_context['month_holidays'] = holidays_dict

        return calendar_context


class MonthWithFormsMixin(MonthCalendarMixin):
    """スケジュール付きの、月間カレンダーを提供するMixin"""

    def get_month_forms(self, start, end, days):
        """それぞれの日と紐づくフォームを作成する"""
        lookup = {
            # '例えば、date__range: (1日, 31日)'を動的に作る
            '{}__range'.format(self.date_field): (start, end)
        }
        # 例えば、Schedule.objects.filter(date__range=(1日, 31日)) になる
        queryset = self.model.objects.filter(**lookup)
        days_count = sum(len(week) for week in days)
        FormClass = forms.modelformset_factory(self.model, self.form_class, extra=days_count)
        if self.request.method == 'POST':
            formset = self.month_formset = FormClass(self.request.POST, queryset=queryset)
        else:
            formset = self.month_formset = FormClass(queryset=queryset)

        # {1日のdatetime: 1日に関連するフォーム, 2日のdatetime: 2日のフォーム...}のような辞書を作る
        day_forms = {day: [] for week in days for day in week}

        # 各日に、新規作成用フォームを1つずつ配置
        for empty_form, (date, empty_list) in zip(formset.extra_forms, day_forms.items()):
            empty_form.initial = {self.date_field: date}
            empty_list.append(empty_form)

        # スケジュールがある各日に、そのスケジュールの更新用フォームを配置
        for bound_form in formset.initial_forms:
            instance = bound_form.instance
            date = getattr(instance, self.date_field)
            day_forms[date].append(bound_form)

        # day_forms辞書を、周毎に分割する。[{1日: 1日のフォーム...}, {8日: 8日のフォーム...}, ...]
        # 7個ずつ取り出して分割しています。
        return [{key: day_forms[key] for key in itertools.islice(day_forms, i, i+7)} for i in range(0, days_count, 7)]

    def get_month_calendar(self):
        calendar_context = super().get_month_calendar()
        month_days = calendar_context['month_days']
        month_first = month_days[0][0]
        month_last = month_days[-1][-1]
        calendar_context['month_day_forms'] = self.get_month_forms(
            month_first,
            month_last,
            month_days
        )
        calendar_context['month_formset'] = self.month_formset
        return calendar_context
