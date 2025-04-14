import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.views import generic
from .forms import BS4ScheduleForm, SimpleScheduleForm
from .models import Schedule
from . import mixins
from .forms import ScheduleDetailForm 
from django.urls import reverse



class MonthCalendar(mixins.MonthCalendarMixin, generic.TemplateView):
    """月間カレンダーを表示するビュー"""
    template_name = 'app/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_month_calendar()
        context.update(calendar_context)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        week_calendar_context = self.get_week_calendar()
        month_calendar_context = self.get_month_calendar()
        context.update(week_calendar_context)
        context.update(month_calendar_context)
        return context

    def form_valid(self, form):
        month = self.kwargs.get('month')
        year = self.kwargs.get('year')
        day = self.kwargs.get('day')
        if month and year and day:
            date = datetime.date(year=int(year), month=int(month), day=int(day))
        else:
            date = datetime.date.today()
        schedule = form.save(commit=False)
        schedule.date = date
        schedule.save()
        return redirect('app:mycalendar', year=date.year, month=date.month, day=date.day)


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
            # コンテキストに 'current_day_date' という名前で追加
            context['current_day_date'] = current_day_date
        except ValueError:
            # URLの日付が無効な場合の処理 (通常はURLパターンで防がれる)
            context['current_day_date'] = None # または Http404 を発生させるなど
        return context

# 編集処理
def schedule_edit(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)

    if request.method == 'POST':
        form = ScheduleDetailForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save()
            return redirect(reverse('app:month_with_schedule', kwargs={
                'year': schedule.date.year,
                'month': schedule.date.month,
            }))
        else:
            print(form.errors)
            context = {'form': form, 'schedule': schedule}
            return render(request, 'app/day.html', context)

    else:
        form = ScheduleDetailForm(instance=schedule)
        context = {'form': form, 'schedule': schedule}
        return render(request, 'app/day.html', context)

# 削除処理
def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        date = schedule.date # 削除前に日付を保持
        schedule.delete()
        return redirect(reverse('app:month_with_schedule', kwargs={
            'year': date.year,
            'month': date.month,
        }))
    # POST 以外のリクエストに対する処理(POST以外だとNoneを返してしまうため)
    return redirect(reverse('app:month_with_schedule', kwargs={'year': schedule.date.year, 'month': schedule.date.month})) # 例: GETなら月表示へ
