function outputData = collapseMeals(inputData)

data = inputData;

minMealDist = 30/data.ts; 

meal = data.meal;
mealFlag = zeros(size(meal));    
isMeal = find(meal>0);
for i = 1:length(isMeal)
    isMealFlag = find(mealFlag>0);
    if i==1 || isMeal(i)-isMealFlag(end)>minMealDist
        mealFlag(isMeal(i)) = 1;
    end
end
data.mealFlag = mealFlag;

outputData = data;
