# FINAL-PROJECT
# The program use the data sources from the A. website:https://www.inaturalist.org/ , which is a citizen science project and online social network of naturalists, citizen scientists and biologists built on the concept of mapping and sharing observations of biodiversity across the globe and B. Web API: Wikipedia, which is a free online encyclopedia, created and edited by volunteers around the world and hosted by Wikimedia Foundation. 

# My codes are structured as following:

# Reptile
# # Part 1 
  # Through the website api, modify the parameters to grab a list of all species of USA birds. The species number can be obtained from the list, and then the URL of the species details page can be constructed.
# # Part 2
  # Visit the details page of each species. View the html source code of the page to find that the basic information of the species is stored in a script tag of the page species, such as biological species, biological picture URL, biological common name and academic name. Because the html contains the data we need to crawl, we use the requests module to request the details page of each creature to get the html. Since our data does not exist in the html tag, there is no need to parse the html. We consider about using regular expressions to do regular matching on the data we need.
# # Part 3
  # Viewing the request data of the detail page through the browser, you can get the statistics API of the creature.Such as biological seasonal habits, frequency of observation, and location of observation.
 
# Data Arrangement and Storage
# # Part 1
  # Since most data is in json format,the result of each request is saved in the format of json file, so as to be called as cache data.

# # Part 2
  # Extract the required data and enter it into sqlite.Request the json data obtained in the first part aextract the required part of the project from it.

# # Part 3
  # Make the tables. 
  
  
# Visualization
  # To make the line charts of each dimension data in the stat_data table to observe the change trend.In addition, the location table is used as a basis to mark the habitat area.
  
# Interactive features
 # The page provides a drop-down option to select different creatures.The charts on the page can be automatically updated according to the change of the creature name in the options.
