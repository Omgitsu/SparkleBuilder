from jinja2 import Template



class Appcast:
    def __init__(self):
    	self.title                              = None
        self.appcast_url                        = None
        self.appcast_description                = None
        self.language                           = None
        self.latest_version_number              = None
        self.latest_version_update_description  = None
        self.pub_date                           = None
        self.latest_version_url                 = None
        self.latest_version_number              = None
        self.latest_version_size                = None
        self.latest_version_dsa_key             = None
        self.release_notes_file                 = None
        self.deltas                             = []

        # appcast main Template
        self.__appcast_template = Template('''
            <rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
            <channel>
            <title>{{ title }}</title>
            <link>{{ appcast_url }}</link>
            <description>{{ appcast_description }}</description>
            <language>{{ language }}</language>
            <item>
            <title>Version {{ latest_version_number }}</title>
            {% if release_notes_file %}
    	    <sparkle:releaseNotesLink>{{ release_notes_file }}</sparkle:releaseNotesLink>
            {% else %}
            <description>{{ latest_version_update_description }}</description>
            {% endif %}
            <pubDate>{{ pub_date }}</pubDate>
            <enclosure url="{{ latest_version_url }}"
                      sparkle:version="{{ latest_version_number }}"
                      length="{{ latest_version_size }}"
                      type="application/octet-stream"
                      sparkle:dsaSignature="{{ latest_version_dsa_key }}"/>
            {% if deltas %}
                <sparkle:deltas>
                {% for delta in deltas %}
                {{ delta }}
                {% endfor %}
                </sparkle:deltas>
            {% endif %}
            </item>
            </channel>
            </rss>
        ''')

    def append_delta(self, delta):
        rendered_delta = delta.render()
        self.deltas.append(rendered_delta)

    def render(self):
        appcast = self.__appcast_template.render(
            title                               = self.title,
            appcast_url                         = self.appcast_url,
            appcast_description                 = self.appcast_description,
            release_notes_file                  = self.release_notes_file,
            launguage                           = self.launguage,
            latest_version_number               = self.latest_version_number,
            latest_version_update_description   = self.latest_version_update_description,
            pub_date                            = self.pub_date,
            latest_version_url                  = self.latest_version_url,
            latest_version_size                 = self.latest_version_size,
            latest_version_dsa_key              = self.latest_version_dsa_key,
            deltas                              = self.deltas,
            )
        return appcast


class Delta:

    def __init__(self):
        self.delta_url              = None
        self.delta_to_version       = None
        self.delta_from_version     = None
        self.delta_size             = None
        self.delta_dsa_key          = None

        self.__delta_template = Template('''
               <enclosure url="{{ delta_url }}"
                          sparkle:version="{{ delta_to_version }}"
                          sparkle:deltaFrom="{{ delta_from_version }}"
                          length="{{ delta_size }}"
                          type="application/octet-stream"
                          sparkle:dsaSignature="{{ delta_dsa_key }}"/>
        ''')

    def render(self):
        delta = self.__delta_template.render(
            delta_url           = self.delta_url,
            delta_to_version    = self.delta_to_version,
            delta_from_version  = self.delta_from_version,
            delta_size          = self.delta_size,
            delta_dsa_key       = self.delta_dsa_key,
            )
        return delta
