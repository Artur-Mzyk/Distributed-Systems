# Distributed-system-for-extraterrestrial-intelligence-search
Repo for project developed during the course "Distributed Systems"

The main objective of this system is to monitor the sky in order to detect radioactivity activity originating from outside our planet. To achieve this, independent research stations (clients) operate autonomously, collecting data on detected activities and transmitting it to a central research unit (server). The collected data from multiple stations is merged and stored in a database, and partial results can be shared and visualized for each connected research station.

Each research station is responsible for observing a specific region of the sky. This region is defined as a rectangle with parameters determined by each station. If a research station detects any data within its designated area, the data is transmitted to the server. If the same area of the sky is observed by multiple research stations, the resulting signal processed on the server will be a combination of all the data provided by the research stations for that particular area.

The collected data is stored in a database, enabling further processing and analysis. The monitoring results can be accessed by system users through a visual interface, allowing for tracking and analysis of radioactivity activity beyond Earth's domain.

The research stations operate independently, meaning that the number of stations does not directly impact the system's operation. However, a larger number of stations may increase the computational time on the computer running the program.
