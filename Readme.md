# Search Engine
*CS 250* - Data Structures and Algorithms - Fall 2024

*Python 3.12.3*

This project involves the making of the search engine using data structures and algorithms that would be most appropriate for the case. The backend is made using **Python** and **Flask** and the frontend is made using simple **HTML**, **CSS** and **Java script**. The dataset used contains features such as title, text, url and more. Through this, we aim to build a search engine that can provide relevant results on a small dataset.

This project is actually inspired by Google's search engine after studying the google's research paper *"<a href="https://www.sciencedirect.com/science/article/abs/pii/S016975529800110X" target="_blank" alt="Paper Link">The Anatomy of the Large Scale Hypertextual Web Search Engine</a>"*. This is an attempt to make similar kind of search engine on a small scale for learning purpose. Therefore, the data structrues used are similar to one's described in the research paper.

## Dataset
The dataset used for this purpose is named *"190K+ Medium Articles Dataset"*. We chose this dataset because firstly, it is neither too small nor too big for a search engine we are making. Secondly, it has some features that would help in process such as title, text, url, and tags. The dataset can be downloaded directly visiting kaggle or the following link: <br>
<a href='https://www.kaggle.com/datasets/fabiochiusano/medium-articles' target="_blank" alt='Dataset Link'>Dataset Download Link</a>
<br><br>
This means by using this dataset, our search engine will only be able to search and show the results for the Medium articles provided in the dataset.

## Prerequisites

Before running the code, make sure you have the following dependencies installed:

- Python (3.x)
- Jupyter Notebook
- Pandas
- Matplotlib
- Seaborn
- Flask
- HTML
- CSS
- Java Script

<br>

## Repository Structure
The repository has been structured in the following way:

- **Notebooks Directory**: This directory contains all the Jupyter Notebooks that were created during the making of the project and to test whether the process is going in the right direction.
- **Templates Directory**: This directory contains the HTML files for frontend web page structure.
- **Static Directory**: This directory contains the CSS styling and Java script files for frontend styling and logic.
- **Python Scripts**: These three files are the actual backend that executes every query the user inputs. The code was obviously reused from the Jupyter notebooks where necessary. The ```app.py``` is the flask file that integrates the frontend and backend, the ```search_engine.py``` is the python script that contains the search logic and as you have guessed, the  ```add_document.py``` is the python script that contains the add document logic.

## Steps Performed
Following is a step-by-step guide that were followed to develop the project:
<ol>
<li>Dataset Cleaning and Preprocessing</li>
<li>Lexicon and Forward Index creation</li>
<li>Inverted Index creation</li>
<li>Barrels creation</li>
<li>Multiple Word Search with Ranking algorithm</li>
<li>Metadata File creation</li>
<li>Add Document logic</li>
<li>Frontend creation (HTML, CSS)</li>
<li>Integration of frontend and backend (Java Script and Flask)</li>
</ol>

For the detailed description of each and every step, consider reading the ```Project Final.pdf``` file.

## Usage
This project has two parts. 

- The first part is the .py files backend which contains the actual logic of the search engine.
- The second part is the frontend which defines the user interface. It takes the input from the user and return relevant search results. To run this UI, run the following commands:
  1. Install the Flask library.
     
     ``` pip install flask ```
     
  2. Locate to the project's directory where the app.py file is located and run:
     
     ``` python app.py ```

     This will open up your browser with UI of the project looking something like this:

     ![image](https://github.com/user-attachments/assets/5ef9c5c5-5efc-4122-b7cb-eeaaf15cc484)

     Any search will provide user with some search results:

     ![image](https://github.com/user-attachments/assets/842514f2-508c-441b-b476-e6ed8025ed7e)


<br>

## Results and Insights
The search engine is providing search results in less than 2 seconds for most of the queries. However, longer queries takes more time. This is due to the fact that each word of the user query is processed separately. This can be made faster by performing parallel processing. The ranking algorithm is too simple but it provides relevant results for most of the cases. But there are some other cases where the ranking algorithm will fail to provide relevant results. The add document logic is working properly but the time it takes is very long. This is due to some unnecessary steps that increases the time.

## Acknowledgments
- This project is inspired by the google's search engine and this is an attempt to make its small scale replica.
- This project is made by the collaboration of <a href="https://github.com/sbukhari23" alt="GitHub link">Muneeb-ur-Rehman</a> and <a href="https://github.com/Hassan-Shahid123" alt="GitHub link">Hassan Shahid</a>.
