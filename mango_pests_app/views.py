# views.py

from django.views.generic import TemplateView, View
from django.shortcuts import render
from .data import mango_threats
from django.core.paginator import Paginator
from django.http import Http404

# Home Page
class HomeView(TemplateView):
    template_name = 'mango_pests_app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['page_title'] = 'Home'
        context['heading'] = "Welcome to the World Mango Organisation of Group 28 of HIT237!"
        context['description'] = "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more about the pests that are consuming our beloved mangos!"
        return context


# Threat List Page
# class ThreatListView(TemplateView):
#     template_name = 'mango_pests_app/threat_list.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         query = self.request.GET.get('q', '').lower()
#         threat_type = self.request.GET.get('category', '').lower()  # Get category filter

#         if query:
#             filtered_threats = [t for t in mango_threats if query in t.name.lower()]
#         else:
#             filtered_threats = mango_threats

#         if threat_type in ['pest', 'disease']:
#             filtered_threats = [t for t in filtered_threats if t.threat_type == threat_type]

        
#         paginator = Paginator(filtered_threats, 10)  # Show 10 items per page
#         page_number = self.request.GET.get('page')  # Get the current page number from the URL
#         page_obj = paginator.get_page(page_number)

#         # Add context variables
#         context['page_title'] = 'Pests and Diseases'
#         context['page_obj'] = page_obj  # Pass the paginated objects to the template
#         context['query'] = query
#         context['threat_type'] = threat_type 
#         return context
    
    
class ThreatListView(TemplateView):
    template_name = 'mango_pests_app/threat_list.html'

    def get_query(self):
        return self.request.GET.get('q', '').lower()

    def get_category(self):
        return self.request.GET.get('category', '').lower()

    def search_threats(self, threats, query):
        if query:
            return [t for t in threats if query in t.name.lower()]
        return threats

    def filter_by_category(self, threats, category):
        if category in ['pest', 'disease']:
            return [t for t in threats if t.threat_type.lower() == category]
        return threats

    def paginate(self, threats):
        paginator = Paginator(threats, 10)
        page_number = self.request.GET.get('page')
        return paginator.get_page(page_number)

    def get_threat_counts(self, threats):
        pest_count = sum(1 for t in threats if t.threat_type.lower() == 'pest')
        disease_count = sum(1 for t in threats if t.threat_type.lower() == 'disease')
        return pest_count, disease_count

    def get_sorting(self):
        return self.request.GET.get('sort', 'name_asc')  # default is A–Z

    def sort_threats(self, threats, sort_option):
        if sort_option == 'name_asc':
            return sorted(threats, key=lambda t: t.name.lower())
        elif sort_option == 'name_desc':
            return sorted(threats, key=lambda t: t.name.lower(), reverse=True)
        return threats


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.get_query()
        category = self.get_category()
        sort_option = self.get_sorting()

        threats = mango_threats
        threats = self.search_threats(threats, query)
        threats = self.filter_by_category(threats, category)
        threats = self.sort_threats(threats, sort_option)  # ✅ sort before paginate

        page_obj = self.paginate(threats)  # ✅ paginate the sorted list
        start_index = page_obj.start_index()
        end_index = page_obj.end_index()

        pest_count, disease_count = self.get_threat_counts(threats)

        context.update({
            'page_title': 'Pests and Diseases',
            'sort_option': sort_option,
            'query': query,
            'threat_type': category,
            'page_obj': page_obj,
            'total_results': len(threats),
            'pest_count': pest_count,
            'disease_count': disease_count,
            'start_index': start_index,
            'end_index': end_index,
        })

        return context



# Threat Details Page
class ThreatDetailView(View):
    def get(self, request, threat_name):
        threat = next((item for item in mango_threats if item.slug == threat_name), None)
        if threat:
            return render(request, 'mango_pests_app/threat_details.html', {'threat': threat})
        else:
            # return render(request, 'mango_pests_app/404.html')
            raise Http404("Threat not found")


class CompareThreatsView(View):
    MAX_SELECTIONS = 3  # Limit the number of threats that can be compared

    def get(self, request):
        return render(request, 'mango_pests_app/compare_threats.html', {'threats': mango_threats})

    def post(self, request):
        selected_slugs = request.POST.getlist('threats')
        
        # Check if the number of selected threats exceeds the limit
        if len(selected_slugs) > self.MAX_SELECTIONS:
            error_message = f"You can only compare up to {self.MAX_SELECTIONS} threats."
            return render(request, 'mango_pests_app/compare_threats.html', {
                'threats': mango_threats,
                'error_message': error_message,
            })
        
        # Get the threats based on selected slugs
        selected_threats = [t for t in mango_threats if t.slug in selected_slugs]
        
        return render(request, 'mango_pests_app/compare_threats.html', {
            'threats': mango_threats,
            'selected_threats': selected_threats,
        })


# About Page
class AboutView(TemplateView):
    template_name = 'mango_pests_app/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "About Us"
        context['team_members'] = [
            {'name': 'Mitchell Danks', 'student_id': 'S320289', 'image': 'aboutmitchell.png'},
            {'name': 'Benjamin Denison-Love', 'student_id': 'S330803', 'image': 'aboutbenjamin.png'},
            {'name': 'Quang Thuan Nguyen', 'student_id': 'S370553', 'image': 'aboutquang.png'},
            {'name': 'Spencer Siu', 'student_id': 'S344930', 'image': 'aboutspencer.png'}
        ]
        return context
