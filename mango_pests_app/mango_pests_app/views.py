from django.views.generic import TemplateView, View
from django.shortcuts import render
from .data import mango_threats
from django.core.paginator import Paginator
from django.http import Http404


# Home Page
class HomeView(TemplateView):
    """
    View for the home page of the Mango Pests & Diseases website.
    Displays a welcome message and introductory content.
    """
    template_name = 'mango_pests_app/home.html'

    def get_context_data(self, **kwargs):
        """
        Add heading and description to the context.

        Returns:
            dict: Context data with heading and description.
        """
        context = super().get_context_data(**kwargs)
        context['heading'] = "Welcome to the World Mango Organisation of Group 28 of HIT237!"
        context['description'] = "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more about the pests that are consuming our beloved mangos!"
        return context


# Threat List Page
class ThreatListView(TemplateView):
    """
    View to display a list of mango threats (pests and diseases).

    Supports search, filtering by type (pest/disease), sorting, and pagination.
    """
    template_name = 'mango_pests_app/threat_list.html'

    def get_query(self):
        """
        Get the search query from the request.

        Returns:
            str: Lowercased search string from the 'q' query parameter.
        """
        return self.request.GET.get('q', '').lower()

    def get_category(self):
        """
        Get the threat category from the request.

        Returns:
            str: Lowercased category string from the 'category' query parameter.
        """
        return self.request.GET.get('category', '').lower()

    def search_threats(self, threats, query):
        """
        Filter threats based on a search query.

        Args:
            threats (list): List of threat objects.
            query (str): Search keyword.

        Returns:
            list: Filtered list of threats.
        """
        if query:
            return [t for t in threats if query in t.name.lower()]
        return threats

    def filter_by_category(self, threats, category):
        """
        Filter threats based on threat type (pest or disease).

        Args:
            threats (list): List of threat objects.
            category (str): 'pest' or 'disease'.

        Returns:
            list: Filtered list of threats.
        """
        if category in ['pest', 'disease']:
            return [t for t in threats if t.threat_type.lower() == category]
        return threats

    def paginate(self, threats):
        """
        Paginate the list of threats.

        Args:
            threats (list): List of threat objects.

        Returns:
            Page: A Django Page object with paginated results.
        """
        paginator = Paginator(threats, 10)
        page_number = self.request.GET.get('page')
        return paginator.get_page(page_number)

    def get_threat_counts(self, threats):
        """
        Count the number of threats by type.

        Args:
            threats (list): List of threat objects.

        Returns:
            tuple: (pest_count, disease_count)
        """
        pest_count = sum(1 for t in threats if t.threat_type.lower() == 'pest')
        disease_count = sum(1 for t in threats if t.threat_type.lower() == 'disease')
        return pest_count, disease_count

    def get_sorting(self):
        """
        Get the sorting option from the request.

        Returns:
            str: Sorting option ('name_asc' or 'name_desc').
        """
        return self.request.GET.get('sort', 'name_asc')

    def sort_threats(self, threats, sort_option):
        """
        Sort threats by name.

        Args:
            threats (list): List of threat objects.
            sort_option (str): Sorting preference.

        Returns:
            list: Sorted list of threats.
        """
        if sort_option == 'name_asc':
            return sorted(threats, key=lambda t: t.name.lower())
        elif sort_option == 'name_desc':
            return sorted(threats, key=lambda t: t.name.lower(), reverse=True)
        return threats

    def get_context_data(self, **kwargs):
        """
        Build context data for the template with filtered, sorted, and paginated threats.

        Returns:
            dict: Context data for rendering the template.
        """
        context = super().get_context_data(**kwargs)

        query = self.get_query()
        category = self.get_category()
        sort_option = self.get_sorting()

        threats = mango_threats
        threats = self.search_threats(threats, query)
        threats = self.filter_by_category(threats, category)
        threats = self.sort_threats(threats, sort_option)

        page_obj = self.paginate(threats)
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
    """
    View to display details of a single threat (pest or disease) based on slug.
    """

    def get(self, request, threat_name):
        """
        Render the details page for a specific threat.

        Args:
            request (HttpRequest): Incoming HTTP request.
            threat_name (str): Slug of the threat.

        Returns:
            HttpResponse: Rendered details page or 404 if not found.
        """
        threat = next((item for item in mango_threats if item.slug == threat_name), None)
        if threat:
            return render(request, 'mango_pests_app/threat_details.html', {'threat': threat})
        else:
            raise Http404("Threat not found")


# Compare Threats Page
class CompareThreatsView(View):
    """
    View to compare selected mango threats.
    Allows comparison of up to MAX_SELECTIONS threats at a time.
    """
    MAX_SELECTIONS = 3  # Limit the number of threats that can be compared

    def get(self, request):
        """
        Render the compare threats page with all threats.

        Returns:
            HttpResponse: Rendered compare page with selection options.
        """
        return render(request, 'mango_pests_app/compare_threats.html', {'threats': mango_threats})

    def post(self, request):
        """
        Handle comparison submission and show selected threats.

        Args:
            request (HttpRequest): Incoming POST request with selected threats.

        Returns:
            HttpResponse: Rendered compare page with selected threats or error message.
        """
        selected_slugs = request.POST.getlist('threats')

        if len(selected_slugs) > self.MAX_SELECTIONS:
            error_message = f"You can only compare up to {self.MAX_SELECTIONS} threats."
            return render(request, 'mango_pests_app/compare_threats.html', {
                'threats': mango_threats,
                'error_message': error_message,
            })

        selected_threats = [t for t in mango_threats if t.slug in selected_slugs]

        return render(request, 'mango_pests_app/compare_threats.html', {
            'threats': mango_threats,
            'selected_threats': selected_threats,
        })


# About Page
class AboutView(TemplateView):
    """
    View for the About Us page.
    Displays team member information and page title.
    """
    template_name = 'mango_pests_app/about.html'

    def get_context_data(self, **kwargs):
        """
        Add team member information to the context.

        Returns:
            dict: Context data with team members and title.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = "About Us"
        context['team_members'] = [
            {'name': 'Mitchell Danks', 'student_id': 'S320289', 'image': 'aboutmitchell.png'},
            {'name': 'Benjamin Denison-Love', 'student_id': 'S330803', 'image': 'aboutbenjamin.png'},
            {'name': 'Quang Thuan Nguyen', 'student_id': 'S370553', 'image': 'aboutquang.png'},
            {'name': 'Spencer Siu', 'student_id': 'S344930', 'image': 'aboutspencer.png'}
        ]
        return context

#Crud Page

class CrudView(TemplateView):
    template_name = 'crud_template.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context