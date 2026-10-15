# Life Expectancy vs. Healthcare Spending

**Author**: Aleyna Alicioglu (i6381736)

**Project**: Small-scale data analysis 

**Course**: Introduction to Programming (MAT2007)

**University**: Maastricht University 


## Research Question
To what extent is the association between healthcare spending and life expectancy characterized by diminishing returns?

## Dataset
The dataset is composed of three indicators: life expectancy at birth, health spending per person, and world region. 

### Cleaning
The script will automatically:
1. Remove any rows with missing values
2. Exclude the countries that have non-positive spendings
3. Filter the data to focus on the year 2019 because it was the last full year before the Covid-19 pandemic. This new sample leaves you with a total of n = 59 countries to analyze.


## Requirements
* Python 3.10 or newer
* Downloadable tools: `numpy`, `pandas`, `scipy` and `matplotlib`

  
## Code Installation

### How to run the code:

### What the script does:
1. Loads and cleans data
2. Filters the data to select the year 2019
3. Creates a scatter plot to visualize the relationship between life expectancy and healthcare spending across 59 countries
4. Fits a linear and a logarithmic model
5. Compares the two models by calculating the coefficient of determination (R²)
6. The second test assumes that there is no curve shape
7. The 59 countries are divided into two equal-sized groups: low- and high-spending
8. The countries are split using the median spending ($2,645)
9. Fits a slope into each spending group with a %95 CI
10. Tests whether there is a significant difference between the two slopes by calculating the z-score
11. Lastly, it prints everything in the terminal and saves the tables and figures


## Results
**Fig. 1. The scatter plot displays life expectancy vs. healthcare spending in the year 2019 with linear and log fits. Each of the 59 dots represents a country in 2019.**

<img width="620" height="380" alt="Screenshot 2026-10-14 at 14 41 00" src="https://github.com/user-attachments/assets/1a704b53-937b-489f-90b4-5e8c65efe1ad" />



**Fig. 2. Two normal distribution curves**

<img width="630" height="352" alt="Screenshot 2026-10-14 at 13 52 17" src="https://github.com/user-attachments/assets/2487d3fc-981b-48a0-91a5-3753ee79f41a" />



## Limitations 



## Conclusion


## Files 


## Data Citation 
