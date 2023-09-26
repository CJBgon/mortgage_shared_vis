from decimal import *
import pandas as pd
def mortgate(
    total_lend,
    interest_rate,
    length,
    ):
    getcontext().rounding = ROUND_UP
    # returns the monthly payment on a mortgage
    length = Decimal(length)
    month_rate = Decimal(interest_rate)/12
    total_months = Decimal(12*length)
    payment = (total_lend*((month_rate*pow((1+month_rate),total_months)) / (pow((1+month_rate),total_months)-1)))
    return payment, payment*total_months # that is the monthly payment over the entire 25 years.

mortgate(
    total_lend=350000,
    interest_rate = 0.033,
    length=25
)



def total_share(
    property_value,
    share_start_per,
    deposit,
    share_buy_percentage,
    rent_percentage = 0.0275,
    property_gains = 0.01,
    mortgage_length = 35,
    mortgage_interest = 0.055,
    service_charge_pcm = 150
    ):

    property_value = Decimal(property_value)
    share_start_per = Decimal(share_start_per)
    deposit = Decimal(deposit)
    share_buy_percentage = Decimal(share_buy_percentage)
    rent_percentage = Decimal(rent_percentage)
    property_gains = Decimal(property_gains)
    mortgage_length = Decimal(mortgage_length)
    mortgage_interest = Decimal(mortgage_interest)
    service_charge_pcm = Decimal(service_charge_pcm)

    share_value_start = (property_value * share_start_per)
    mortgage_amount = (share_value_start - deposit)

    # calculate monthly and total costs of the mortgage.
    # assuming the interest rate remains the same over the entire duration.
    mortgage_pcm, mortgage_total = mortgate(
        total_lend = mortgage_amount,
        interest_rate = mortgage_interest,
        length=mortgage_length
        )

    # we pay off shares every X time period, reducing the outstanding shares and thus the rent_pcm.
    # does the total property value at the start have to be paid? Or the total value adjusted for price increases each year?
    # for year in range(1,years_till_completion):
    outstanding_shares = property_value - share_value_start
    adjusted_outstanding_shares = outstanding_shares
    adjusted_property_value = property_value
    # cummulative_bought = 0
    rent_annual = [Decimal(0)]
    property_value_col = [property_value]
    outstanding_shares_col = [outstanding_shares]
    # cummulative_share_paid = [deposit]
    share_paid = [deposit]
    # year=[0]
    time=0

    while adjusted_outstanding_shares > Decimal(2000):
        time +=1
        # year.append(time)
        # pay rent on the remaining outstanding shares.
        rent_ann = adjusted_outstanding_shares * rent_percentage
        rent_annual.append(rent_ann)
        # rent_pcm = rent_ann / 12
        # property value goes up
        # each year the property goes up or own in value based on the price adjust
        adjusted_property_value += (adjusted_property_value * property_gains)  # we don't care about the total property value - just the remaining shares
        property_value_col.append(adjusted_property_value)
        adjusted_outstanding_shares += (adjusted_outstanding_shares * property_gains)
        
        # here we are buying based on a percentage of outstanding shares. 
        # Shouldn't we base it on adjusted property value?
        share_buy = adjusted_property_value * share_buy_percentage
        adjusted_outstanding_shares -= share_buy
        outstanding_shares_col.append(adjusted_outstanding_shares)

        # cummulative_bought += share_buy
        # cummulative_share_costs.append(cummulative_bought)
        # more usfull to say how much we paid in shares that year.
        share_paid.append(share_buy)

    share_frame = pd.DataFrame(
        {
            # 'year':year,
            'property_value':property_value_col,
            'outstanding_shares':outstanding_shares_col,
            'share_paid':share_paid,
            'annual_rent':rent_annual,
        })
    # add in the service charge.
    share_frame['service_charge'] = service_charge_pcm
    # remove the negative oustanding shares from the share paid.
    overpaid = share_frame.loc[share_frame['outstanding_shares'] < Decimal(0), 'outstanding_shares'].item()
    share_frame.loc[share_frame['outstanding_shares'] < Decimal(0), 'outstanding_shares'] = Decimal(0)
    share_frame.loc[share_frame['outstanding_shares'] < Decimal(0), 'share_paid'] += overpaid

    # put in a mortgage costs calculation.
    mortgage_payment_annual = [Decimal(0)]
    mortgage_total_count = mortgage_total 
    while mortgage_total_count > Decimal(1):
        mortgage_payment_annual.append(mortgage_pcm*Decimal(12))
        mortgage_total_count -= mortgage_pcm*Decimal(12)

    full_df = pd.concat([share_frame, pd.Series(mortgage_payment_annual, name='annual_mortgage')], axis=1)

    # check if the share-table is shorter than the mortgage table
    # if the mortgage table is shorter fillna with 0s.
    # if the share-table is shorter fill specific columns

    if len(mortgage_payment_annual) < share_frame.shape[0]:
        full_df['annual_mortgage'].fillna(Decimal(0), inplace=True)
    elif len(mortgage_payment_annual) > share_frame.shape[0]:
        full_df['property_value'].fillna(share_frame.iloc[-1,1], inplace=True)
        full_df['outstanding_shares'].fillna(Decimal(0),inplace=True)
        full_df['share_paid'].fillna(Decimal(0),inplace=True)
        full_df['annual_rent'].fillna(Decimal(0),inplace=True)
        full_df['service_charge'].fillna(Decimal(0),inplace=True)


    full_df['total_costs'] = (
        full_df['share_paid']
        + full_df['annual_rent'] 
        + full_df['annual_mortgage']
        )
    full_df['cummulative_costs'] = full_df['total_costs'].cumsum()
    full_df.reset_index(inplace=True)
    full_df.rename({'index':'year'}, axis=1, inplace=True)

    return full_df


# testing.

# lets say we get a 3 bedroom property of value 650 000
# a full mortgage with a deposit of 100K over 25 years would be:
def calc_mortgage_costs(
    total_lend,
    interest_rate,
    length
    ):
    mortgage_pcm, mortgage_total = mortgate(
        total_lend,
        interest_rate,
        length
        )
    mortgage_df = pd.DataFrame({
        'year':range(0,length),
    })
    mortgage_df['annual_mortgage']=mortgage_pcm*12
    mortgage_df['cummulative_costs']=mortgage_df['annual_mortgage'].cumsum()
    return (mortgage_df)


# compare to the share_buy scheme.
share_df = total_share(
    property_value=650000,
    share_start_per=0.50,
    share_buy_percentage=0.05,
    property_gains=0.03,
    deposit=100000,
    mortgage_length=25,
    mortgage_interest=0.06,
    service_charge_pcm=150)



import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons

axis_color = 'lightgoldenrodyellow'
fig = plt.figure()
ax = fig.add_subplot(111)

# Adjust the subplots region to leave some space for the sliders and buttons
fig.subplots_adjust(left=0.25, bottom=0.5)

total_lend_0=650000
interest_rate_0=0.06
length_0=25

prop_value_0=650000
start_per_0=0.50
share_buy_perc_0=0.05
prop_gains_0=0.01
deposit_0=100000
shared_morg_len_0=10
service_charge_0=150

[line_mortgage] = ax.plot(
    calc_mortgage_costs(
        total_lend_0,
        interest_rate_0,
        length_0)['year'],
    calc_mortgage_costs(
        total_lend_0,
        interest_rate_0,
        length_0)['cummulative_costs'], 
    linewidth=2, 
    color='orange')

[line_shared] = ax.plot(
    total_share(
        property_value=Decimal(prop_value_0),
        share_start_per=Decimal(start_per_0),
        share_buy_percentage=Decimal(share_buy_perc_0),
        property_gains=Decimal(prop_gains_0),
        deposit=deposit_0,
        mortgage_length=shared_morg_len_0,
        mortgage_interest=interest_rate_0,
        service_charge_pcm=service_charge_0)['year'],
    total_share(
        property_value=Decimal(prop_value_0),
        share_start_per=Decimal(start_per_0),
        share_buy_percentage=Decimal(share_buy_perc_0),
        property_gains=Decimal(prop_gains_0),
        deposit=deposit_0,
        mortgage_length=shared_morg_len_0,
        mortgage_interest=interest_rate_0,
        service_charge_pcm=service_charge_0)['cummulative_costs'],
        )


ax.set_xlim([0, 50])
ax.set_ylim([0, 1.5e6])


# Define an axes area and draw a slider in it
####################### mortgate sliders ########################
lend_slider_ax  = fig.add_axes([0.25, 0.45, 0.65, 0.03], facecolor=axis_color)
lend_slider = Slider(lend_slider_ax, 'Mortgage lend', 300000, 800000, valinit=total_lend_0, valstep=10000)

interest_slider_ax  = fig.add_axes([0.25, 0.40, 0.65, 0.03], facecolor=axis_color)
interest_slider = Slider(interest_slider_ax, 'interest_rate', 0.01, 0.10, valinit=interest_rate_0, valstep=0.005)

length_slider_ax  = fig.add_axes([0.25, 0.35, 0.65, 0.03], facecolor=axis_color)
length_slider = Slider(length_slider_ax, 'Private - Mortgate length', 5, 50, valinit=length_0, valstep=1)

######################## shared sliders ##########################
prop_slider_ax  = fig.add_axes([0.25, 0.30, 0.65, 0.03], facecolor=axis_color)
prop_slider = Slider(prop_slider_ax, 'Property value', 300000, 800000, valinit=prop_value_0, valstep=10000)

deposit_slider_ax  = fig.add_axes([0.25, 0.25, 0.65, 0.03], facecolor=axis_color)
deposit_slider = Slider(deposit_slider_ax, 'Deposit', 10000, 150000, valinit=deposit_0, valstep=1000)

startper_slider_ax  = fig.add_axes([0.25, 0.20, 0.65, 0.03], facecolor=axis_color)
startper_slider = Slider(startper_slider_ax, 'Property start percentage', 0.05, 0.95, valinit=start_per_0, valstep=0.05)

sharebuy_slider_ax  = fig.add_axes([0.25, 0.15, 0.65, 0.03], facecolor=axis_color)
sharebuy_slider = Slider(sharebuy_slider_ax, 'Annual percentage shares ', 0.01, 0.5, valinit=share_buy_perc_0, valstep=0.01)

propgains_slider_ax  = fig.add_axes([0.25, 0.1, 0.65, 0.03], facecolor=axis_color)
propgains_slider = Slider(propgains_slider_ax, 'Property gains', 0.01, 0.10, valinit=prop_gains_0, valstep=0.01)

shared_length_slider_ax  = fig.add_axes([0.25, 0.05, 0.65, 0.03], facecolor=axis_color)
shared_length_slider = Slider(shared_length_slider_ax, 'Shared - Mortgate length', 5, 50, valinit=shared_morg_len_0, valstep=1)




# how to detect what value changed? as we need two values...
def sliders_on_changed(val):  
    line_mortgage.set_data(
        calc_mortgage_costs(
            Decimal(lend_slider.val),
            Decimal(interest_slider.val),
            length_slider.val)['year'],
        calc_mortgage_costs(
            Decimal(lend_slider.val),
            Decimal(interest_slider.val),
            length_slider.val)['cummulative_costs']
            )
    line_shared.set_data(
    total_share(
        property_value=Decimal(prop_slider.val),
        share_start_per=Decimal(startper_slider.val),
        share_buy_percentage=Decimal(sharebuy_slider.val),
        property_gains=Decimal(propgains_slider.val),
        deposit=deposit_slider.val,
        mortgage_length=shared_length_slider.val,
        mortgage_interest=interest_slider.val,
        service_charge_pcm=service_charge_0)['year'],
   total_share(
        property_value=Decimal(prop_slider.val),
        share_start_per=Decimal(startper_slider.val),
        share_buy_percentage=Decimal(sharebuy_slider.val),
        property_gains=Decimal(propgains_slider.val),
        deposit=deposit_slider.val,
        mortgage_length=shared_length_slider.val,
        mortgage_interest=interest_slider.val,
        service_charge_pcm=service_charge_0)['cummulative_costs'],
        )
    
    # line_mortgage.set_xdata(
    #     calc_mortgage_costs(
    #         Decimal(lend_slider.val),
    #         Decimal(interest_slider.val),
    #         Decimal(length_slider.val))['year']
    #         )
    fig.canvas.draw_idle()

lend_slider.on_changed(sliders_on_changed)
interest_slider.on_changed(sliders_on_changed)
length_slider.on_changed(sliders_on_changed)
prop_slider.on_changed(sliders_on_changed)
deposit_slider.on_changed(sliders_on_changed)
startper_slider.on_changed(sliders_on_changed)
sharebuy_slider.on_changed(sliders_on_changed)
propgains_slider.on_changed(sliders_on_changed)
shared_length_slider.on_changed(sliders_on_changed)

reset_button_ax = fig.add_axes([0.8, 0.025, 0.1, 0.04])
reset_button = Button(reset_button_ax, 'Reset', color=axis_color, hovercolor='0.975')

def reset_button_on_clicked(mouse_event):
    lend_slider.reset()
    interest_slider.reset()
    length_slider.reset()
    prop_slider.reset()
    deposit_slider.reset()
    startper_slider.reset()
    sharebuy_slider.reset()
    propgains_slider.reset()
    shared_length_slider.reset()
reset_button.on_clicked(reset_button_on_clicked)
plt.xlabel("years")
plt.ylabel("total costs")
plt.legend()
plt.show()

