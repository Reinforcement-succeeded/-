from django.shortcuts import render
from run_model import sentiment_predict
import csv
# from django.utils import timezone
from user.models import CustomUser
from .models import Category, Store
from review.models import Review
import random
from datetime import datetime
from django.db.models import Avg, Prefetch


# from run_model import sentiment_predict

def today_ranking():
    all_reviews = Review.objects.filter(create_date__gte=datetime(2022, 5, 10), create_date__lte=datetime(2022, 6, 10))
    order_volume = {}
    for ar in all_reviews:
        if ar.store.category.name in order_volume:
            order_volume[ar.store.category.name] += 1
        else:
            order_volume[ar.store.category.name] = 1
    order_volume2 = list(sorted(order_volume.items(), key=lambda x: x[1], reverse=True))
    if len(order_volume2) > 5:
        return order_volume2[:5]
    else:
        return order_volume2


def today_review():
    all_reviews = Review.objects.all().filter(star=5)
    return random.choice(all_reviews)


def period_ranking():
    filterStore = Review.objects.filter(create_date__gte=datetime(2022, 6, 4),
                                        create_date__lte=datetime(2022, 6, 10)).select_related('store').all()
    PeriodRanking = {}
    for fs in filterStore:
        if fs.store.name in PeriodRanking:
            PeriodRanking[fs.store.name][0][0] += fs.star
            PeriodRanking[fs.store.name][0][1] += 1
        else:
            PeriodRanking[fs.store.name] = [[fs.star, 1], fs.store.category.name]
    for PR in PeriodRanking:
        PeriodRanking[PR] = [PeriodRanking[PR][0][0] / PeriodRanking[PR][0][1], PeriodRanking[PR][1]]
    PeriodRankingList = []
    for p in PeriodRanking:
        PeriodRankingList.append([p, PeriodRanking[p][0], PeriodRanking[p][1]])
    PeriodRankingList.sort(reverse=True, key=lambda x: x[1])
    if len(PeriodRankingList) > 5:
        return PeriodRankingList[:5]
    else:
        return PeriodRankingList


# Create your views here.
def main_view(request):
    input = {}
    #카테고리 집어 넣기
    all_category = Category.objects.all()
    for ac in all_category:
        if input == {}:
            input['category'] = [ac.name]
        else:
            input['category'].append(ac.name)
    #오늘의 리뷰 넣기
    review = today_review()
    input['today_review'] = review
    #오늘의 주문랭킹
    ranking = today_ranking()
    input['today_ranking'] = ranking
    return render(request, 'main/main.html', {'data':input})





def category_result_view(request, category):
    input = {}
    # 카테고리 집어 넣기
    input['category'] = [category]
    # 오늘의 리뷰 넣기
    review = today_review()
    input['today_review'] = review
    # 오늘의 주문랭킹
    ranking = today_ranking()
    input['today_ranking'] = ranking
    # 카테고리에 맞는 가게 찾기
    catMatchStore = Store.objects.all().filter(category=Category.objects.get(name=category))
    cms = catMatchStore.annotate(average=Avg('review__star'))
    # 가게에 맞는 댓글 넣기
    # a= cms.prefetch_related('review_set').all()
    cms = cms.prefetch_related(
        Prefetch(
            'review_set',
            queryset=Review.objects.all(),
            to_attr='reviews'
        )
    )
    input['store'] = cms
    # 주소 넣기
    location = []
    for c in cms:
        location.append(c.location)
    input['location'] = set(location)
    # 최근 먹음 음식 순위 #일단 일주일 기준
    input['periodRanking'] = period_ranking()
    return render(request, 'result/result.html', {'data': input})


def mood_result_view(request):
    if request.method == 'POST':
        input = {}
        # 점수에 맞게 가게 찾기
        print('number')
        print(request.POST.get('number'))
        user_mood = int(request.POST.get('number'))
        if user_mood < 50:
            user_mood = 100 - user_mood
        averageStore = Store.objects.all().annotate(average=Avg('review__calc_star'))
        filterStore = averageStore.filter(average__gte=user_mood - 10,
                                          average__lte=user_mood + 10)
        filterStore = filterStore.prefetch_related(
            Prefetch(
                'review_set',
                queryset=Review.objects.all(),
                to_attr='reviews'
            )
        )
        input['store'] = filterStore
        # 찾은 가게에서 카테고리 넣기
        category = []
        location = []
        for f in filterStore:
            category.append(f.category.name)
            location.append(f.location)
        input['category'] = set(category)
        input['location'] = set(location)
        # 오늘의 리뷰 넣기
        review = today_review()
        input['today_review'] = review
        # 오늘의 주문랭킹
        ranking = today_ranking()
        input['today_ranking'] = ranking
        # 최근 먹음 음식 순위 #일단 일주일 기준
        input['periodRanking'] = period_ranking()
        return render(request, 'result/result.html', {'data': input})


def location_result_view(request):
    if request.method == 'POST':
        input = {}
        user_location = request.POST.get('text')
        filterStore = Store.objects.all().filter(location=user_location).annotate(average=Avg('review__star'))
        filterStore = filterStore.prefetch_related(
            Prefetch(
                'review_set',
                queryset=Review.objects.all(),
                to_attr='reviews'
            )
        )
        input['store'] = filterStore
        # 찾은 가게에서 카테고리 넣기
        category = []
        location = []
        for f in filterStore:
            category.append(f.category.name)
            location.append(f.location)
        input['category'] = set(category)
        input['location'] = set(location)
        # 오늘의 리뷰 넣기
        review = today_review()
        input['today_review'] = review
        # 오늘의 주문랭킹
        ranking = today_ranking()
        input['today_ranking'] = ranking
        # 최근 먹음 음식 순위 #일단 일주일 기준
        input['periodRanking'] = period_ranking()
        return render(request, 'result/result.html', {'data': input})
