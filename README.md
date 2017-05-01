# Files (in order of execution)

## Import Sources (importSources.py)

### Overview

This is the first file run after the database setup and the json files from OpenSources.co are downloaded. This file iterates through all websites, both credible and non credible and searches the source code for rss feed URLs. Once the sites are all searched the source data is saved in the database.

### Outputs

None

## Read Feeds

### Overview

Now that the sources and feeds have been saved into the database this file will iterate through the feeds and get all the articles and save the data into the articles table of the database. Additionally, this script will call the Google Natural Language Processing API and get the entities from the title and description of each article. The script will then classify words as "who," "what," and "where" based on the results and store them accordingly in the database.

### Outputs

None

## Form Term Maps

### Overview

This script iterates through all the articles gathered and analyzes the title and description. First, the script removes all stop words from both strings. Next, the script stems the words. Then, the script counts the frequency of each word and normalizes the frequency by dividing it by the total number of words. This value will now act as the word's score or importance. After, the script iterates through all entities deemed important by Google's NLP API and multiplies the score of those words by 1.5 to mark them as vital. The scores are now sorted and the top 8 words are saved in a JSON object for that article in the database.

### Outputs

None

## Form Article Links

### Overview

This script forms a network of articles where the weights of the edges connecting the articles are between 0 and 30 and are higher when the two articles are more similar. Sometimes duplicate articles come up where the edge weight is exactly 30. In this case, one of the duplicates are removed from the pool. The weights are formed by calculating the cosine similarity between the word vectors of the two articles. Once calculated the weights are then saved in another table in the database.

### Output

None

## Cumulative Edge Distro SQL Procedure

### Overview

This is a SQL procedure that will give stats on the network connecting articles together. Specifically, this will iterate through 1 to 30 using variable i and filter out and link with a weight less than i. Then, it will tally out how many links remain and what the density is of the graph as links are filtered out while nodes remain untouched.

### Output

SQL result which is saved as `data/query_result.csv` and used to form `visualizations/eventFormationFiltering.png`

## Form Events

### Overview

This script starts by setting a threshold value which is formed based on the results of the previous SQL procedure. Then the script gets all article links with a weight greater then the threshold. This decreases the amount of data that needs to be processed and lets us focus on the important links between articles. 

Once the edges are returned and parsed the node data is pulled from the database. This includes the source title and article title for each article. That data is then added to the edge data and a networkx graph is formed. 

Now the orphan nodes are removed from the graph to once again make the amount of data more reasonable to process. This means that only articles with a lot in common with each other will remain. In this case that is still a substantial amount. 

The next step is to perform heirarchical agglomerative clustering on the article graph. This will form clusters that can represent the common events that the articles are discussing. Once the dendrogram is formed the script uses modularity calculations to find which cluster level to use. Now that the clusters are formed the graph is saved both as a gml file and in the database.

### Output

`data/article-similarities{threshold}.gml` - Graph of the article links after filtered down

`visualizations/articleLinksDendrogram.png` - Dendrogram of the heirarchical clustering

`visualizations/modularities.png` - Graph of the modularity values

`visualizations/articleLinksSnapshot.png` - Gephi representation of the article links graph

## Form Event Attrs

### Overview

This script associates the top keywords with each event as well as the number of articles for each event. The results are saved in the database.

### Output

None

## Analyze Events

### Overview

This script parses the results from the previous two scripts and forms a networkx graph where nodes represent both events and sources and the edges connecting them are the articles. The weight of the edges is how many articles there are connecting the source and the event.

With the graph formed, centralities are calculated including hub value, authority value, degree, eigenvector centrality, and a custom centrality. The custom centrality takes into account a threshold value and assigns a score to each node. The score is calculated by comparing the weights of all edges from the node with the threshold value. If the weight is lower, the node's score decreases. However, if the weight is greater, the node's score increases greatly.

Finally, a confusion matrix is formed with all the centrality values. The test claims that all sources marked credible by opensources.co are credible as well as the events they reported on. This will provide a good baseline of what centrality value should be used. The classification of credible or not credible is done using a range of threshold values for each centrality. Then, the classification is compared to the opensources data to produce the confusion matrix data.

### Output

`data/sourceEvents.gml` - This is the networkx graph formed between sources and events

`data/nodes.csv` - Stats of all nodes in the graph mentioned above.

`analysis-{centrality}.csv` - The confusion matrix results for that particular centrality.

`visualizations/eventSourceSnapshot.png` - The confusion matrix results for the custom centrality at a threshold value of 10.

`visualizations/analysis-custom-10.png` - The confusion matrix results for the custom centrality at a threshold value of 10.

