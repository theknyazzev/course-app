from django.core.management.base import BaseCommand
from learning_platform.models import Category, Video

class Command(BaseCommand):
    help = 'Create test data for the learning platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))

        # Create categories if they don't exist
        categories_data = [
            ('html_css', 'Web development basics: HTML structure and CSS styling'),
            ('javascript', 'JavaScript programming and interactivity'),
            ('php', 'Server-side programming with PHP and databases'),
            ('wordpress', 'WordPress website creation, themes and plugins'),
        ]
        
        for name, description in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created category: {category.get_name_display()}')

        # Create test videos
        videos_data = [
            # HTML + CSS
            ('HTML Lesson 1: HTML Introduction', 'Learn HTML basics, document structure and basic tags.', 'html_css', 'https://www.youtube.com/watch?v=example1'),
            ('HTML Lesson 2: Working with Forms', 'Creating forms, input fields and user data handling.', 'html_css', 'https://www.youtube.com/watch?v=example2'),
            ('CSS Lesson 1: Styling Basics', 'Introduction to CSS, selectors and basic style properties.', 'html_css', 'https://www.youtube.com/watch?v=example3'),
            ('CSS Lesson 2: Flexbox and Grid', 'Modern layout methods with Flexbox and CSS Grid.', 'html_css', 'https://www.youtube.com/watch?v=example4'),
            
            # JavaScript
            ('JavaScript Lesson 1: Variables and Functions', 'Learn JavaScript basics: variables, data types and functions.', 'javascript', 'https://www.youtube.com/watch?v=example5'),
            ('JavaScript Lesson 2: DOM Manipulation', 'Working with DOM elements, events and interactivity.', 'javascript', 'https://www.youtube.com/watch?v=example6'),
            ('JavaScript Lesson 3: Asynchronous Programming', 'Promises, async/await and API integration.', 'javascript', 'https://www.youtube.com/watch?v=example7'),
            
            # PHP
            ('PHP Lesson 1: Syntax Basics', 'Learn PHP syntax, variables and basic constructions.', 'php', 'https://www.youtube.com/watch?v=example8'),
            ('PHP Lesson 2: Working with Forms', 'Form data processing and user input validation.', 'php', 'https://www.youtube.com/watch?v=example9'),
            ('PHP Lesson 3: MySQL Databases', 'Database connection and SQL query execution.', 'php', 'https://www.youtube.com/watch?v=example10'),
            
            # WordPress
            ('WordPress Lesson 1: Installation and Setup', 'WordPress installation and basic site configuration.', 'wordpress', 'https://www.youtube.com/watch?v=example11'),
            ('WordPress Lesson 2: Working with Themes', 'Choosing and customizing website themes.', 'wordpress', 'https://www.youtube.com/watch?v=example12'),
        ]

        for title, description, category_name, video_url in videos_data:
            try:
                category = Category.objects.get(name=category_name)
                video, created = Video.objects.get_or_create(
                    title=title,
                    defaults={
                        'description': description,
                        'category': category,
                        'video_url': video_url,
                        'is_published': True
                    }
                )
                if created:
                    self.stdout.write(f'Created video: {title}')
                else:
                    self.stdout.write(f'Video already exists: {title}')
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Category {category_name} not found'))

        self.stdout.write(self.style.SUCCESS(f'Total videos in database: {Video.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
