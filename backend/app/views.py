from collections import defaultdict
from datetime import timedelta
import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.views import generic
from .forms import BS4ScheduleForm, SimpleScheduleForm
from .models import Schedule
from . import mixins
from .forms import ScheduleDetailForm 
from django.urls import reverse
from datetime import timedelta, time

# class MonthCalendar(mixins.MonthCalendarMixin, generic.TemplateView):
#     """月間カレンダーを表示するビュー"""
#     template_name = 'app/month.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         week_calendar_context = self.get_week_calendar()
#         month_calendar_context = self.get_month_calendar()
#         context.update(week_calendar_context)
#         context.update(month_calendar_context)

#         # スケジュールの再構築（end_date 跨ぎ対応）
#         week_first = context['week_first']
#         week_last = context['week_last']

#         # スケジュール取得：その週に1日でもかかっているもの
#         schedules = Schedule.objects.filter(
#             end_datetime__date__gte=week_first,
#             start_datetime__date__lte=week_last,
#         ).order_by('start_datetime', 'end_datetime')

#         # スケジュールを日付ごとに分配
#         week_day_schedules = defaultdict(list)
#         for schedule in schedules:
#             current = schedule.start_datetime.date()
#             while current <= schedule.end_datetime.date():
#                 if week_first <= current <= week_last:
#                     week_day_schedules[current].append(schedule)
#                 current += timedelta(days=1)
        
#         # 日付ごとにソート
#         for day, day_schedules in week_day_schedules.items():
#             week_day_schedules[day] = sorted(day_schedules, key=lambda x: (x.start_datetime.time(), x.end_datetime.time()))
        
#         context['week_day_schedules'] = week_day_schedules
#         return context


# class WeekCalendar(mixins.WeekCalendarMixin, generic.TemplateView):
#     """週間カレンダーを表示するビュー"""
#     template_name = 'app/week.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         calendar_context = self.get_week_calendar()
#         context.update(calendar_context)
#         return context


class WeekWithScheduleCalendar(mixins.WeekWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの週間カレンダーを表示するビュー"""
    template_name = 'app/week_with_schedule.html'
    model = Schedule
    date_field = 'start_datetime'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_week_calendar()
        context.update(calendar_context)
        week_data = zip(self.get_week_names(), self.get_week_days())
        context["week_data"] = list(week_data)
        return context


class MonthWithScheduleCalendar(mixins.MonthWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの月間カレンダーを表示するビュー"""
    template_name = 'app/month_with_schedule.html'
    model = Schedule
    date_field = 'start_datetime'

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
    date_field = 'start_datetime'
    form_class = BS4ScheduleForm

    def get_initial(self):
        initial = super().get_initial()
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year and month and day:
            target_date = datetime.date(int(year), int(month), int(day))
            initial['start_datetime'] = target_date
            initial['end_datetime'] = target_date
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        week_calendar_context = self.get_week_calendar()
        month_calendar_context = self.get_month_calendar()
        context.update(week_calendar_context)
        context.update(month_calendar_context)

        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')

        if year and month and day:
            target_date = datetime.date(int(year), int(month), int(day))
            context['target_date'] = target_date
        return context

    def form_valid(self, form):
        start_datetime = form.cleaned_data['start_datetime']
        end_datetime = form.cleaned_data['end_datetime']
        summary = form.cleaned_data['summary']
        description = form.cleaned_data['description']
        date = form.cleaned_data['start_datetime'].date()
        reminder_enabled = form.cleaned_data.get('reminder_enabled', True)

        schedule = Schedule(
            summary=summary,
            description=description,
            date=date,
            start_datetime= start_datetime,
            end_datetime = end_datetime,
            reminder_enabled=reminder_enabled,
        )
        schedule.save()

        return redirect(reverse('app:month_with_schedule', args=[start_datetime.year, start_datetime.month]))


class MonthWithFormsCalendar(mixins.MonthWithFormsMixin, generic.View):
    """フォーム付きの月間カレンダーを表示するビュー"""
    template_name = 'app/month_with_forms.html'
    model = Schedule
    date_field = 'start_datetime'
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
    
class DayDetailCalendar(mixins.WeekWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの日間カレンダーを表示するビュー"""
    template_name = 'app/dayDetail.html'
    model = Schedule
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        pk = self.kwargs.get('pk')
        schedule = get_object_or_404(Schedule, pk=pk, date__year=year, date__month=month, date__day=day)
        context['schedule'] = schedule
        
        try:
            current_day_date = datetime.date(year, month, day)
            context['current_day_date'] = current_day_date
        except ValueError:
            context['current_day_date'] = None # または Http404 を発生させるなど
        return context

class DayCalendar(mixins.WeekWithScheduleMixin, generic.TemplateView):
    """スケジュール付きの日間カレンダーを表示するビュー"""
    template_name = 'app/day.html'
    model = Schedule
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        pk = self.kwargs.get('pk')
        schedule = get_object_or_404(Schedule, pk=pk, date__year=year, date__month=month, date__day=day)
        context['schedule'] = schedule
        
        try:
            current_day_date = datetime.date(year, month, day)
            context['current_day_date'] = current_day_date
        except ValueError:
            context['current_day_date'] = None # または Http404 を発生させるなど
        
        context['form'] = ScheduleDetailForm(instance=schedule)
        
        return context

# 編集処理
def schedule_edit(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)

    if request.method == 'POST':
        form = ScheduleDetailForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save()
            return redirect(reverse('app:month_with_schedule', kwargs={
                'year': form.cleaned_data['start_datetime'].year,
                'month': form.cleaned_data['start_datetime'].month,
        }))
        else:
            print(form.errors)
            context = {'form': form, 'schedule': schedule, 'current_day_date': schedule.date}
            return render(request, 'app/day.html', context)

    else:
        form = ScheduleDetailForm(instance=schedule)
        context = {'form': form, 'schedule': schedule, 'current_day_date': schedule.date }
        return render(request, 'app/day.html', context)

# 削除処理
def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        date = schedule.date
        schedule.delete()
        return redirect(reverse('app:month_with_schedule', kwargs={
            'year': date.year,
            'month': date.month,
        }))
    return redirect(reverse('app:month_with_schedule', kwargs={'year': schedule.date.year, 'month': schedule.date.month}))
