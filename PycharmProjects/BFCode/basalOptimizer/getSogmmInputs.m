function inputs = getSogmmInputs(data)

meals = find(data.mealFlag>0);
nmeals = length(meals);
meals = [meals; length(data.cgm)+1];

inputs = zeros(length(data.cgm),nmeals+1);
inputs(:,1) = data.basal+data.bolus;

dMeal1 = 5/data.ts;
dMeal2 = 15/data.ts;

for i = 1:nmeals
    currMeal = meals(i);
    nextMeal = meals(i+1)-1;
    for j = currMeal:nextMeal
        dMeal = dMeal1*(data.meal(j)*data.ts/1000<=15)+dMeal2*(data.meal(j)*data.ts/1000>15);
        inputs(j:min(j+dMeal-1,length(data.cgm)),i+1) = inputs(j:min(j+dMeal-1,length(data.cgm)),i+1)+data.meal(j)/dMeal;
    end
end
