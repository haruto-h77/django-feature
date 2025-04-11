from collections import defaultdict
from datetime import timedelta
import datetime
from django.shortcuts import redirect, render
from django.views import generic
from .forms import BS4ScheduleForm, SimpleScheduleForm
from .models import Schedule
from . import mixins

class MonthCalendar(mixins.MonthCalendarMixin, generic.TemplateView):
    """月間カレンダーを表示するビュー"""
    template_name = 'app/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        week_calendar_context = self.get_week_calendar()
        month_calendar_context = self.get_month_calendar()
        context.update(week_calendar_context)
        context.update(month_calendar_context)

        # スケジュールの再構築（end_date 跨ぎ対応）
        week_first = context['week_first']
        week_last = context['week_last']

        # スケジュール取得：その週に1日でもかかっているもの
        schedules = Schedule.objects.filter(
            end_date__gte=week_first,
            start_date__lte=week_last,
        )

        # スケジュールを日付ごとに分配
        week_day_schedules = defaultdict(list)
        for schedule in schedules:
            current = schedule.start_date
            while current <= schedule.end_date:
                if week_first <= current <= week_last:
                    week_day_schedules[current].append(schedule)
                current += timedelta(days=1)

        context['week_day_schedules'] = week_day_schedules
        return context


class WeekCalendar(mixins.WeekCalendarMixin, generic.TemplateView):
    """週間カレンダーを表示するビュー"""
    template_name = 'app/week.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_week_calendar()
        context.update(calendar_context)
        return context


class WeekWithScheduleCalendar(mixins.WeekWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの週間カレンダーを表示するビュー"""
    template_name = 'app/week_with_schedule.html'
    model = Schedule
    date_field = 'date'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_week_calendar()
        context.update(calendar_context)
        return context


class MonthWithScheduleCalendar(mixins.MonthWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの月間カレンダーを表示するビュー"""
    template_name = 'app/month_with_schedule.html'
    model = Schedule
    date_field = 'date'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_month_calendar()
        context.update(calendar_context)
        context['month_numbers'] = range(1, 13) # 1から12までの数字のリストを追加
        return context


class MyCalendar(mixins.MonthCalendarMixin, mixins.WeekWithScheduleMixin, generic.CreateView):
    """月間カレンダー、週間カレンダー、スケジュール登録画面のある欲張りビュー"""
    template_name = 'app/mycalendar.html'
    model = Schedule
    date_field = 'date'
    form_class = BS4ScheduleForm

    def get_initial(self):
        initial = super().get_initial()
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year and month and day:
            target_date = datetime.date(int(year), int(month), int(day))
            initial['start_date'] = target_date
            initial['end_date'] = target_date
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        week_calendar_context = self.get_week_calendar()
        month_calendar_context = self.get_month_calendar()
        context.update(week_calendar_context)
        context.update(month_calendar_context)
        return context

    def form_valid(self, form):
        # month = self.kwargs.get('month')
        # year = self.kwargs.get('year')
        # day = self.kwargs.get('day')     
        # フォームからstart_date, end_dateを取得
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        summary = form.cleaned_data['summary']
        description = form.cleaned_data['description']

        # 日付が一致する場合（単一日付の場合）も考慮して、開始日から終了日までの間の日を登録
        current_date = start_date
        while current_date <= end_date:
                    # 毎回新しいScheduleインスタンスを作成
            schedule = Schedule(
                summary=summary,
                description=description,
                date=current_date,
                start_date=start_date,
                end_date=end_date,
            )
            # schedule = form.save(commit=False)
            # schedule.date = current_date  # ここで現在の日付をセット
            # schedule.start_date = start_date
            # schedule.end_date = end_date
            schedule.save()
            current_date += timedelta(days=1)  # 1日ずつ増加
        # if month and year and day:
        #     date = datetime.date(year=int(year), month=int(month), day=int(day))
        # else:
        #     date = datetime.date.today()
        # schedule = form.save(commit=False)
        # schedule.date = date
        # schedule.save()
        return redirect('app:mycalendar', year=start_date.year, month=start_date.month, day=start_date.day)


class MonthWithFormsCalendar(mixins.MonthWithFormsMixin, generic.View):
    """フォーム付きの月間カレンダーを表示するビュー"""
    template_name = 'app/month_with_forms.html'
    model = Schedule
    date_field = 'date'
    form_class = SimpleScheduleForm

    def get(self, request, **kwargs):
        context = self.get_month_calendar()
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        context = self.get_month_calendar()
        formset = context['month_formset']
        if formset.is_valid():
            formset.save()
            return redirect('app:month_with_forms')

        return render(request, self.template_name, context)
