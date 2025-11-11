{
    'name': 'Chatbot Platform',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'B2B Chatbot Platform with RAG and Vector Search',
    'description': """
        Multi-tenant B2B chatbot platform where users can create chatbots,
        add documents/links, and embed them on their websites with API key authentication.
        
        Features:
        - Chatbot management
        - Document and link processing
        - API key generation
        - Automatic synchronization with FastAPI
        - Embeddable widgets
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'web'],
    'data': [
        'security/chatbot_security.xml',
        'security/ir.model.access.csv',
        'views/chatbot_views.xml',
        'views/document_views.xml',
        'views/menu_views.xml',
        'data/chatbot_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
