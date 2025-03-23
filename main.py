import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Israel Suicide Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set default template for plotly figures
template = dict(
    layout=dict(
        font=dict(color='black'),
        title=dict(font=dict(color='black')),
        xaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
        yaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
        legend=dict(font=dict(color='black'))
    )
)


def update_fig_layout(fig):
    """Update figure layout to ensure all text is black"""
    fig.update_layout(
        font_color='black',
        title_font_color='black',
        legend_font_color='black',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    fig.update_xaxes(title_font_color='black', tickfont_color='black')
    fig.update_yaxes(title_font_color='black', tickfont_color='black')
    return fig


# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Load data
@st.cache_data
def load_data():
    try:
        # Load the main datasets
        suicides_gender = pd.read_csv('data/output_folder/Suicides per Gender.csv')
        suicides_age_gender = pd.read_csv('data/output_folder/Suicides - Age&Gender.csv')
        attempts_age_gender = pd.read_csv('data/output_folder/Attempts - Age&Gender.csv')
        ethnic_groups = pd.read_csv('data/output_folder/Suicides - Ethnic Groups.csv')

        return {
            'suicides_gender': suicides_gender,
            'suicides_age_gender': suicides_age_gender,
            'attempts_age_gender': attempts_age_gender,
            'ethnic_groups': ethnic_groups
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


@st.cache_data
def load_ethnic_data():
    try:
        suicides_ethnic_groups = pd.read_csv('data/output_folder/Suicides - Ethnic Groups.csv')
        attempts_ethnic_groups = pd.read_csv('data/output_folder/Attempts - Ethnic Groups.csv')

        suicides_olim = pd.read_csv('data/output_folder/Suicides - Olim.csv')
        attempts_olim = pd.read_csv('data/output_folder/Olim - Attempts.csv')

        # Ensure year column is numeric and sorted
        for df in [suicides_ethnic_groups, suicides_olim, attempts_olim]:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df.dropna(subset=['year'], inplace=True)
            df.sort_values(by='year', inplace=True)

        return {
            'suicides_ethnic_groups': suicides_ethnic_groups,
            'attempts_ethnic_groups': attempts_ethnic_groups,
            'suicides_olim': suicides_olim,
            'attempts_olim': attempts_olim
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def main():
    # Header
    st.markdown('<h1 class="main-header">Israel Suicide Data Analysis Dashboard</h1>', unsafe_allow_html=True)

    # Load data
    data = load_data()
    if not data:
        st.error("Failed to load data. Please check if the CSV files are in the correct location.")
        return

    # Set sidebar width using custom CSS
    st.markdown(
        """
    <style>
    /* Fix sidebar width and remove expand/collapse button */
    [data-testid="stSidebar"] {
        width: 290px !important;
    }
    [data-testid="stSidebar"] button[title="Hide sidebar"], 
    [data-testid="stSidebar"] button[title="Show sidebar"] {
        display: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.markdown("## Dashboard Controls")

        # Section selector
        selected_section = st.selectbox(
            "Choose Section",
            ["Overview", "Time Trends", "Age Analysis", "Demographic Analysis"]
        )

        # Year range selector
        years = sorted(data['suicides_gender']['year'].unique())
        start_year, end_year = st.select_slider(
            'Select Year Range',
            options=years,
            value=(min(years), max(years))
        )

        st.markdown("""<p style="font-size: 15px;">💡 <b>Tip</b>: Use the side menu to switch between different views and adjust the time range</p>""",
                    unsafe_allow_html=True)

    # Filter data by year range
    filtered_gender = data['suicides_gender'][
        (data['suicides_gender']['year'] >= start_year) &
        (data['suicides_gender']['year'] <= end_year)
        ]

    selected_age_groups = None
    # Display selected section
    if selected_section == "Overview":
        display_overview(filtered_gender, data)
    elif selected_section == "Age Analysis":
        # Get the age group with maximum suicides
        age_cols = ['<14', '15-17', '18-21', '22-24', '25-44', '45-64', '65-74', '75+']
        age_gender_data = data['suicides_age_gender'].copy()
        age_gender_data['year'] = pd.to_numeric(age_gender_data['year'], errors='coerce')
        filtered_data = age_gender_data[(age_gender_data['year'] >= start_year) &
                                        (age_gender_data['year'] <= end_year) &
                                        (age_gender_data['group'] == 'all')]

        avg_by_age = filtered_data[age_cols].mean()
        max_suicide_age_group = avg_by_age.idxmax()

        st.markdown("## Age Groups for Analysis")
        st.markdown("Select age groups for in-depth analysis:")

        selected_age_groups = st.multiselect(
            "Select Age Groups",
            options=age_cols,
            default=[max_suicide_age_group],
            help="The age group with the highest suicide rate is selected by default. You can select additional groups."
        )
        display_age_analysis(data, start_year, end_year, selected_age_groups)
    elif selected_section == "Demographic Analysis":
        display_demographic_analysis(data, start_year, end_year)
    else:
        display_time_trends(data, start_year, end_year)


def display_overview(filtered_gender, data):
    latest_year = filtered_gender['year'].max()
    first_year = filtered_gender['year'].min()
    latest_data = filtered_gender[filtered_gender['year'] == latest_year]

    st.markdown(f'<h2 class="sub-header">Overview of Suicide Data for the year : {latest_year}</h2>',
                unsafe_allow_html=True)

    # Add explanation
    st.markdown("""
    This section shows key suicide statistics and trends in Israel, with current metrics and their changes from previous years.

    """)

    # KPI metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"Total Suicides ({latest_year})",
            value=f"{int(latest_data['total_num'].iloc[0]):,}",
            delta=f"{(latest_data['total_num'].iloc[0] - filtered_gender[filtered_gender['year'] == latest_year - 1]['total_num'].iloc[0]):.0f} compared to {latest_year - 1}",
            delta_color="inverse"
        )

    with col2:
        st.metric(
            label="Male Suicides",
            value=f"{int(latest_data['men_num'].iloc[0]):,}",
            delta=f"{(latest_data['men_num'].iloc[0] - filtered_gender[filtered_gender['year'] == latest_year - 1]['men_num'].iloc[0]):.0f} compared to {latest_year - 1}",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="Female Suicides",
            value=f"{int(latest_data['women_num'].iloc[0]):,}",
            delta=f"{(latest_data['women_num'].iloc[0] - filtered_gender[filtered_gender['year'] == latest_year - 1]['women_num'].iloc[0]):.0f} compared to {latest_year - 1}",
            delta_color="inverse"
        )

    with col4:
        st.metric(
            label="Total Rate (per 100k)",
            value=f"{latest_data['total_rate'].iloc[0]:.1f}",
            delta=f"{(latest_data['total_rate'].iloc[0] - filtered_gender[filtered_gender['year'] == latest_year - 1]['total_rate'].iloc[0]):.1f} compared to {latest_year - 1}",
            delta_color="inverse"
        )

    # Trend charts
    col1, col2 = st.columns(2)

    tick_positions = np.linspace(first_year, latest_year, num=5, dtype=int)

    with col1:
        fig = px.line(
            filtered_gender,
            x='year',
            y=['men_rate', 'women_rate'],
            title='Suicide Rates by Gender Over Time',
            labels={
                'value': 'Rate per 100,000',
                'year': 'Year',
                'men_rate': 'Male Rate',
                'women_rate': 'Female Rate',
                'variable': 'Gender'
            },
            color_discrete_sequence=['blue', 'red'],
            template='plotly_white'
        )

        fig.update_traces(
            hovertemplate="<b>%{y:.1f}</b> per 100,000<br>" +
                          "Year: %{x}<br>"
        )

        fig.update_xaxes(
            tickvals=tick_positions,  # Explicit tick positions
            ticktext=[str(year) for year in tick_positions],  # Convert to string for labels
            range=[first_year - 0.5, latest_year + 1],
        )

        fig = update_fig_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(filtered_gender, x='year', y=['men_num', 'women_num'],
                     # subtitle=f'between {filtered_gender["year"].min()} and {filtered_gender["year"].max()}',
                     title='Number of Suicides by Gender',
                     labels={'value': 'Number of Suicides',
                             'year': 'Year',
                             'men_num': 'Male',
                             'women_num': 'Female',
                             'variable': 'Gender'},
                     color_discrete_sequence=['blue', 'red'],
                     template='plotly_white')

        fig.update_traces(
            hovertemplate="<b>%{y}</b> suicides<br>" +
                          "Year: %{x}<br>"
        )

        fig.update_xaxes(
            tickvals=tick_positions,  # Explicit tick positions
            ticktext=[str(year) for year in tick_positions],  # Convert to string for labels
            range=[first_year - 0.5, latest_year + 1],
        )

        fig = update_fig_layout(fig)
        st.plotly_chart(fig, use_container_width=True)


def display_age_analysis(data, start_year, end_year, selected_age_groups=None):
    st.markdown('<h2 class="sub-header">Suicide Rates by Age Group</h2>', unsafe_allow_html=True)
    st.markdown("""
    This section explores suicide rates across different age groups, identifying trends over time.
    """)

    age_gender_data = data['suicides_age_gender'].copy()
    age_gender_data['year'] = pd.to_numeric(age_gender_data['year'], errors='coerce')
    age_gender_data = age_gender_data[(age_gender_data['year'] >= start_year) & (age_gender_data['year'] <= end_year)]

    age_cols = ['<14', '15-17', '18-21', '22-24', '25-44', '45-64', '65-74', '75+']

    # Calculate average suicides by age group for the selected period
    avg_by_age = age_gender_data[age_gender_data['group'] == 'all'][age_cols].mean()
    avg_by_age_df = pd.DataFrame({
        'Age Group': age_cols,
        'Average Suicides': avg_by_age.values
    })

    # Sort by suicide count in descending order
    avg_by_age_df = avg_by_age_df.sort_values(by='Average Suicides', ascending=True)

    # Create a color list - red for the first bar, blue for the rest
    colors = ['#1f77b4'] * (len(avg_by_age_df) - 1) + ['red']

    # Create horizontal bar chart
    st.markdown("### Suicide Distribution by Age Group")

    fig = px.bar(avg_by_age_df,
                 x='Average Suicides',
                 y='Age Group',
                 title=f'Average Suicides by Age Group ({start_year}-{end_year})',
                 orientation='h',
                 template='plotly_white',
                 text='Average Suicides')

    # Update bar colors - first bar red, others default blue
    for i, bar in enumerate(fig.data[0].marker.color):
        fig.data[0].marker.color = colors

    # Configure text display
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')

    fig = update_fig_layout(fig)
    fig.update_layout(
        xaxis_title="Average Suicides",
        xaxis_tickfont=dict(color='black'),
        xaxis_title_font=dict(color='black'),
        yaxis_title="Age Group",
        yaxis_tickfont=dict(color='black'),
        yaxis_title_font=dict(color='black'),
        uniformtext_minsize=10,  # Minimum text size
        uniformtext_mode='hide',  # Hide text if it doesn't fit
        height=500,  # Increase height
        autosize=True  # Allow autosize instead of fixed width
    )

    # Use the full container width
    st.plotly_chart(fig, use_container_width=True)

    # Add tip after the graph
    st.markdown("""
    💡 **Tip**: Select age groups in the side menu for in-depth analysis.
    """)

    # Display selected age groups or prompt to select
    if selected_age_groups and len(selected_age_groups) > 0:
        st.markdown("### Selected Age Groups for In-Depth Analysis")
        st.write(f"Selected age groups: {', '.join(selected_age_groups)}")

        # Create a divider
        st.markdown("---")

        # Create 3 columns for additional graphs
        st.markdown("### In-Depth Analysis by Selected Age Groups")

        # Create a 3-column layout for the additional graphs
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### Suicides Over Time")

            # Filter data for selected age groups and create time series
            if selected_age_groups:
                # Get data for all years for the selected age groups
                all_years_data = data['suicides_age_gender'].copy()
                all_years_data['year'] = pd.to_numeric(all_years_data['year'], errors='coerce')
                all_years_data = all_years_data[all_years_data['group'] == 'all']

                # Create a line chart for selected age groups over time
                fig_time = px.line(
                    all_years_data,
                    x='year',
                    y=selected_age_groups,
                    title=f'Suicides Over Time by Selected<br> Age Groups',
                    labels={'year': 'Year', 'value': 'Number of Suicides', 'variable': 'Age Group'},
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    template='plotly_white'
                )

                # Apply custom styling to ensure all text is black
                fig_time.update_layout(
                    xaxis_title="Year",
                    yaxis_title="Number of Suicides",
                    legend_title="Age Group",
                    height=400,  # Increase height from 300 to 400
                    margin=dict(l=10, r=10, t=50, b=50),
                    font=dict(color='black'),
                    title_font_color='black',
                    legend_font_color='black',
                    xaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    yaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    legend=dict(
                        font=dict(color='black'),
                        title_font=dict(color='black')
                    )
                )

                tick_positions = np.linspace(start_year, end_year, num=5, dtype=int)

                fig_time.update_xaxes(
                    tickvals=tick_positions,  # Explicit tick positions
                    ticktext=[str(year) for year in tick_positions],  # Convert to string for labels
                    range=[start_year - 0.5, end_year + 1],
                    tickangle=-45,  # Rotate labels for readability
                 )

                # Make sure plot background and paper background are white
                fig_time.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )

                st.plotly_chart(fig_time, use_container_width=True)
            else:
                # Placeholder if no age groups selected
                st.markdown(
                    """
                    <div style="
                        height: 400px;
                        width: 100%;
                        border: 2px dashed #aaa;
                        border-radius: 5px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        color: #888;
                        font-size: 16px;
                        text-align: center;
                        padding: 20px;
                    ">
                    Please select at least one age group in the side menu
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col2:
            st.markdown("##### Attempts vs. Suicides")

            # Filter data for selected age groups and create comparison
            if selected_age_groups:
                # Get suicide data
                suicide_data = age_gender_data[age_gender_data['group'] == 'all'].copy()

                # Get attempt data
                attempts_data = data['attempts_age_gender'].copy()
                attempts_data['year'] = pd.to_numeric(attempts_data['year'], errors='coerce')
                attempts_data = attempts_data[(attempts_data['year'] >= start_year) &
                                              (attempts_data['year'] <= end_year) &
                                              (attempts_data['group'] == 'all')]

                # Create a dataframe for comparison
                comparison_data = []

                # Map age columns from attempts to match suicides
                age_map = {
                    '10-14': '<14',  # Closest match
                    '15-17': '15-17',
                    '18-21': '18-21',
                    '22-24': '22-24',
                    '25-44': '25-44',
                    '45-64': '45-64',
                    '65-74': '65-74',
                    '75+': '75+'
                }

                # Calculate average for each selected age group
                for age_group in selected_age_groups:
                    # For suicides
                    suicide_avg = suicide_data[age_group].mean()

                    # For attempts - find the matching column
                    attempt_col = None
                    for attempt_age, suicide_age in age_map.items():
                        if suicide_age == age_group:
                            attempt_col = attempt_age
                            break

                    # If we found a matching column, calculate average
                    attempt_avg = 0
                    if attempt_col and attempt_col in attempts_data.columns:
                        attempt_avg = attempts_data[attempt_col].mean()

                    # Add to comparison data
                    comparison_data.append({
                        'Age Group': age_group,
                        'Type': 'Completed Suicides',
                        'Average': suicide_avg
                    })
                    comparison_data.append({
                        'Age Group': age_group,
                        'Type': 'Suicide Attempts',
                        'Average': attempt_avg
                    })

                # Create DataFrame
                comparison_df = pd.DataFrame(comparison_data)

                # Create grouped bar chart
                fig_comparison = px.bar(
                    comparison_df,
                    x='Age Group',
                    y='Average',
                    color='Type',
                    barmode='group',
                    title=f'Suicide Attempts vs. Completed Suicides by<br>Age Group ({start_year}-{end_year})',
                    color_discrete_map={
                        'Completed Suicides': '#FF4136',  # Red
                        'Suicide Attempts': '#0074D9'  # Blue
                    },
                    template='plotly_white',
                    text='Average'  # Add text to display values
                )

                # Configure text display
                fig_comparison.update_traces(texttemplate='%{text:.1f}', textposition='outside')

                # Apply styling to ensure all text is black
                fig_comparison.update_layout(
                    xaxis_title="Age Group",
                    yaxis_title="Average",
                    legend_title="Type",
                    height=400,  # Increase height from 300 to 400
                    margin=dict(l=10, r=10, t=50, b=50),
                    font=dict(color='black'),
                    title_font_color='black',
                    legend_font_color='black',
                    xaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    yaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    legend=dict(
                        font=dict(color='black'),
                        title_font=dict(color='black')
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    uniformtext_minsize=8,  # Minimum text size
                    uniformtext_mode='hide'  # Hide text if it doesn't fit
                )

                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                # Placeholder if no age groups selected
                st.markdown(
                    """
                    <div style="
                        height: 400px;
                        width: 100%;
                        border: 2px dashed #aaa;
                        border-radius: 5px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        color: #888;
                        font-size: 16px;
                        text-align: center;
                        padding: 20px;
                    ">
                    Please select at least one age group in the side menu
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col3:
            st.markdown("##### Suicides by Gender")

            # Filter data for selected age groups and create gender comparison
            if selected_age_groups:
                # Get data for men
                men_data = data['suicides_age_gender'].copy()
                men_data['year'] = pd.to_numeric(men_data['year'], errors='coerce')
                men_data = men_data[(men_data['year'] >= start_year) &
                                    (men_data['year'] <= end_year) &
                                    (men_data['group'] == 'men')]

                # Get data for all (to calculate women by subtraction)
                all_data = data['suicides_age_gender'].copy()
                all_data['year'] = pd.to_numeric(all_data['year'], errors='coerce')
                all_data = all_data[(all_data['year'] >= start_year) &
                                    (all_data['year'] <= end_year) &
                                    (all_data['group'] == 'all')]

                # Create a dataframe for gender comparison
                gender_data = []

                # Calculate average for each selected age group
                for age_group in selected_age_groups:
                    # For men
                    men_avg = men_data[age_group].mean()

                    # For all
                    all_avg = all_data[age_group].mean()

                    # Calculate women by subtraction
                    women_avg = all_avg - men_avg

                    # Add to gender data
                    gender_data.append({
                        'Age Group': age_group,
                        'Gender': 'Men',
                        'Average Suicides': men_avg
                    })
                    gender_data.append({
                        'Age Group': age_group,
                        'Gender': 'Women',
                        'Average Suicides': women_avg
                    })

                # Create DataFrame
                gender_df = pd.DataFrame(gender_data)

                # Create grouped bar chart
                fig_gender = px.bar(
                    gender_df,
                    x='Age Group',
                    y='Average Suicides',
                    color='Gender',
                    barmode='group',
                    title=f'Suicides by Gender and <br>Age Group ({start_year}-{end_year})',
                    color_discrete_map={
                        'Men': '#3366CC',  # Blue
                        'Women': '#FF6699'  # Pink
                    },
                    template='plotly_white',
                    text='Average Suicides'  # Add text to display values
                )

                # Configure text display
                fig_gender.update_traces(texttemplate='%{text:.1f}', textposition='outside')

                # Apply styling to ensure all text is black
                fig_gender.update_layout(
                    xaxis_title="Age Group",
                    yaxis_title="Average Suicides",
                    legend_title="Gender",
                    height=400,  # Increase height from 300 to 400
                    margin=dict(l=10, r=10, t=50, b=50),
                    font=dict(color='black'),
                    title_font_color='black',
                    legend_font_color='black',
                    xaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    yaxis=dict(
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    legend=dict(
                        font=dict(color='black'),
                        title_font=dict(color='black')
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    uniformtext_minsize=8,  # Minimum text size
                    uniformtext_mode='hide'  # Hide text if it doesn't fit
                )

                st.plotly_chart(fig_gender, use_container_width=True)
            else:
                # Placeholder if no age groups selected
                st.markdown(
                    """
                    <div style="
                        height: 400px;
                        width: 100%;
                        border: 2px dashed #aaa;
                        border-radius: 5px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        color: #888;
                        font-size: 16px;
                        text-align: center;
                        padding: 20px;
                    ">
                    Please select at least one age group in the side menu
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        # Display message when no age groups are selected
        st.markdown("### Select Age Groups for In-Depth Analysis")
        st.info("Please select one or more age groups in the side menu to view detailed analysis.")


def display_demographic_analysis(data, start_year, end_year):
    st.markdown('<h2 class="sub-header">Demographic Analysis</h2>', unsafe_allow_html=True)

    # Add explanation
    st.markdown("""
    Analysis of suicide patterns across different age groups and ethnic populations in Israel.

    💡 **Tip**: Adjust the time range in the side menu to explore demographic trends over different periods.
    """)

    # Filter age-gender data
    age_gender_data = data['suicides_age_gender'].copy()
    # Convert year to numeric if needed
    age_gender_data['year'] = pd.to_numeric(age_gender_data['year'], errors='coerce')
    age_gender_data = age_gender_data[
        (age_gender_data['year'] >= start_year) &
        (age_gender_data['year'] <= end_year)
    ]

    # Age distribution
    st.markdown("### Age Distribution of Suicides")

    age_cols = ['<14', '15-17', '18-21', '22-24', '25-44', '45-64', '65-74', '75+']
    latest_year_data = age_gender_data[age_gender_data['year'] == age_gender_data['year'].max()]

    fig = px.bar(latest_year_data, x=age_cols, y='total',
                 title=f"Age Distribution of Suicides ({latest_year_data['year'].iloc[0]})",
                 labels={'value': 'Number of Suicides', 'variable': 'Age Group'},
                 color_discrete_sequence=px.colors.qualitative.Set3,
                 template='plotly_white')

    fig = update_fig_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Ethnic groups comparison
    ethnic_data = data['ethnic_groups'].copy()
    # Convert year to numeric if needed
    ethnic_data['year'] = pd.to_numeric(ethnic_data['year'], errors='coerce')
    ethnic_data = ethnic_data[
        (ethnic_data['year'] >= start_year) &
        (ethnic_data['year'] <= end_year)
    ]

    st.markdown("### Suicide Rates by Ethnic Group")

    fig = px.line(ethnic_data, x='year', y='total', color='ethnicity',
                  title='Suicide Trends by Ethnic Group',
                  labels={'total': 'Number of Suicides', 'year': 'Year'},
                  color_discrete_sequence=px.colors.qualitative.Set1,
                  template='plotly_white')

    fig = update_fig_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

def display_time_trends(data, start_year, end_year):
    st.markdown('<h2 class="sub-header">Time Trends Analysis</h2>', unsafe_allow_html=True)

    # Add explanation
    st.markdown("""
    Temporal analysis of suicide attempts across different age groups, showing historical patterns and trends.

    💡 **Tip**: Use the year range selector to focus on specific time periods of interest.
    """)

    # Monthly trends
    attempts_monthly = data['ethnic_groups'].copy()

    # Filter based on the numeric year column
    attempts_monthly = attempts_monthly[
        (attempts_monthly['year'] >= start_year) &
        (attempts_monthly['year'] <= end_year)
    ]

    st.markdown("### Suicide Attempts Over Time")

    fig = px.line(attempts_monthly, x='year', y='total',
                  title='Total Suicide Attempts by Year',
                  labels={'year': 'Year', 'total': 'Number of Attempts'},
                  color_discrete_sequence=['darkblue'],
                  template='plotly_white')

    fig = update_fig_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Age group trends
    st.markdown("### Trends by Age Group")

    age_cols = ['10-14', '15-17', '18-21', '22-24', '25-44', '45-64', '65-74', '75+']
    fig = px.line(attempts_monthly, x='year', y=age_cols,
                  title='Suicide Attempts by Age Group',
                  labels={'year': 'Year', 'value': 'Number of Attempts'},
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  template='plotly_white')

    fig = update_fig_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

def display_demographic_analysis(data, start_year, end_year):
    st.markdown('<h1 class="main-header">Israel Suicide Data Analysis Dashboard</h1>', unsafe_allow_html=True)

    data = load_ethnic_data()
    if not data:
        st.error("Failed to load data. Please check if the CSV files are in the correct location.")
        return

    # Filter data by year range
    suicides_filtered = data['suicides_ethnic_groups'][
        (data['suicides_ethnic_groups']['year'] >= start_year) &
        (data['suicides_ethnic_groups']['year'] <= end_year)
        ]

    attempts_filtered = data['attempts_ethnic_groups'][
        (data['attempts_ethnic_groups']['year'] >= start_year) &
        (data['attempts_ethnic_groups']['year'] <= end_year)
        ]

    # Main Chart: Suicide Rates Over Time by Ethnicity
    st.markdown("### Suicide and Attempts Trends Over Time by Ethnic Group and Gender")

    # Toggle between suicide attempts and completed suicides inside page
    st.markdown("### Select Data Type")
    chart_type = st.radio(
        "Choose data type:",
        ["Completed Suicides", "Suicide Attempts"],
        horizontal=True
    )

    if chart_type == "Completed Suicides":
        chart_data = suicides_filtered.copy()
        my_title = "Suicide Trends Over Time by Ethnic Group and Gender"
    else:  # "Suicide Attempts"
        chart_data = attempts_filtered.copy()
        my_title = "Suicide <u>Attempts</u> Trends Over Time by Ethnic Group and Gender"

    if "ethnicity" in chart_data.columns and "group" in chart_data.columns:
        # Create a new column that combines ethnicity and gender
        chart_data['ethnicity_gender'] = chart_data['ethnicity'] + ' - ' + chart_data['group']

        # Create custom color mapping
        color_map = {
            'Jews & Christians - men': '#0039a6',  # Dark blue for Jewish men
            'Jews & Christians - women': '#71a5de',  # Light blue for Jewish women
            'Arabs - men': '#b22222',  # Dark red for Arab men
            'Arabs - women': '#ff7f7f'  # Light red for Arab women
        }
        # Define the order for the legend
        category_order = [
            'Jews & Christians - men',
            'Jews & Christians - women',
            'Arabs - men',
            'Arabs - women'
        ]

        fig = px.line(
            chart_data,
            x="year",
            y="total",
            color="ethnicity_gender",
            color_discrete_map=color_map,
            markers=True,
            title=my_title,
            category_orders={"ethnicity_gender": category_order}
        )

        min_year = chart_data['year'].min()
        max_year = chart_data['year'].max()

        # Update x-axis to show all years with increments of 1
        fig.update_xaxes(
            dtick=1,  # Set tick interval to 1 year
            tick0=min_year,  # Start ticks at the minimum year
            range=[min_year - 0.5, max_year + 0.5],  # Extend range slightly for better visualization
            tickangle=-45,  # Rotate labels by 45 degrees
            tickmode='linear'  # Ensure all ticks are shown
        )

        fig.update_yaxes(
            range=[0,
                   # 100 + chart_data['total'].max()
                   650]
        )

        fig = update_fig_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid data available for ethnic groups.")

    st.markdown("---")

    st.markdown("### Suicide Attempts vs. Completed Suicides among Newcomers")

    # Calculate percentages for completed suicides
    suicides_pct = data['suicides_olim'].copy()
    suicides_pct['total'] = suicides_pct['Ethiopia'] + suicides_pct['USSR'] + suicides_pct['Others']
    suicides_pct['Ethiopia_pct'] = suicides_pct['Ethiopia'] / suicides_pct['total']
    suicides_pct['USSR_pct'] = suicides_pct['USSR'] / suicides_pct['total']
    suicides_pct['Others_pct'] = suicides_pct['Others'] / suicides_pct['total']
    suicides_pct['data_type'] = 'Completed Suicides'

    # Process suicide attempts data
    attempts_pct = data['attempts_olim'][data['attempts_olim']['group'] == 'all'].copy()  # Only use 'all' group

    # Convert string values with apostrophes to numeric
    for col in ['ethiopia_since_1980', 'ussr_since_1990', 'other_immigrants']:
        # Try to convert to numeric, coercing errors to NaN
        attempts_pct[col] = pd.to_numeric(attempts_pct[col].astype(str).str.strip("'"), errors='coerce')

    # Calculate total attempts and percentages
    attempts_pct['Total'] = attempts_pct['ethiopia_since_1980'] + attempts_pct['ussr_since_1990'] + attempts_pct[
        'other_immigrants']

    attempts_pct['Ethiopia_pct'] = attempts_pct['ethiopia_since_1980'] / attempts_pct['Total']
    attempts_pct['USSR_pct'] = attempts_pct['ussr_since_1990'] / attempts_pct['Total']
    attempts_pct['Others_pct'] = attempts_pct['other_immigrants'] / attempts_pct['Total']
    attempts_pct['data_type'] = 'Attempts'

    # Create dataframes with only the columns we need for visualization
    suicides_for_vis = suicides_pct[['year', 'Ethiopia_pct', 'USSR_pct', 'Others_pct', 'data_type']]
    attempts_for_vis = attempts_pct[['year', 'Ethiopia_pct', 'USSR_pct', 'Others_pct', 'data_type']]

    # Rename columns for consistency
    suicides_for_vis = suicides_for_vis.rename(columns={
        'Ethiopia_pct': 'Ethiopia', 'USSR_pct': 'USSR', 'Others_pct': 'Others'
    })

    attempts_for_vis = attempts_for_vis.rename(columns={
        'Ethiopia_pct': 'Ethiopia', 'USSR_pct': 'USSR', 'Others_pct': 'Others'
    })

    # Combine both datasets
    combined_data = pd.concat([suicides_for_vis, attempts_for_vis])

    # Convert to long format for Plotly
    combined_data_long = pd.melt(
        combined_data,
        id_vars=['year', 'data_type'],
        value_vars=['Ethiopia', 'USSR', 'Others'],
        var_name='Origin',
        value_name='Percentage'
    )

    # Convert year to string for categorical display
    combined_data_long['year'] = combined_data_long['year'].astype(str)

    # Create the stacked bar chart
    fig = px.bar(
        combined_data_long,
        y='year',
        x='Percentage',
        color='Origin',
        facet_col='data_type',
        orientation='h',
        # title="Proportion of Suicides and Attempts<br>                by Country of Origin",
        title="Proportion of Suicides and Attempts by Country of Origin",
        color_discrete_map={
            "Ethiopia": "#F4A261",  # Warm orange
            "USSR": "#2A9D8F",  # Teal
            "Others": "#264653"  # Deep blue
        },
        # facet_col_spacing=0.15  # Adjust gap between subplots (default is 0.03)
    )

    # Update layout for better visualization
    fig.update_layout(
        barmode='stack',
        # height=500,
        legend_title="Country of Origin",
        # margin=dict(l=50, r=50, t=80, b=50)
    )

    # Update x-axis to show percentages
    fig.update_xaxes(
        title="Percentage",
        tickformat='.0%',
        title_standoff=5,  # Reduce spacing
        # tickfont=dict(size=8)  # Scale down font size
    )

    # Update y-axis - reverse order to show most recent years at the top
    fig.update_yaxes(
        categoryorder='category descending',
        showticklabels=True
    )

    # Hide y-axis labels for all but the first facet
    fig.for_each_yaxis(lambda y: y.update(showticklabels=False) if y.anchor != 'x' else None)

    # Remove "data_type=" from facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

    st.plotly_chart(fig, use_container_width=True)

    # st.markdown("""
    # **Key observations:**
    # - Former USSR immigrants consistently represent the largest proportion of both suicide attempts and completions
    # - Ethiopian immigrants show a higher percentage in completed suicides compared to their representation in attempts
    # - The "Others" category represents a smaller proportion of both attempts and completions
    # - There is year-to-year variation in the proportions, particularly in completed suicides
    # """)

    # Right Chart: Suicide Rates by Gender and Ethnicity
    # with col2:
    #     st.markdown("### Suicide Rates by Gender and Ethnicity")
    #
    #     if "year" in gender_ethnicity_filtered.columns and "Men" in gender_ethnicity_filtered.columns and "Women" in gender_ethnicity_filtered.columns:
    #         gender_ethnicity_chart = px.line(
    #             gender_ethnicity_filtered, x='year', y=['Men', 'Women'],
    #             title='Suicide Rates by Gender and Ethnicity',
    #             markers=True,
    #             labels={'year': 'Year', 'value': 'Suicide Rate', 'variable': 'Gender'},
    #             template='plotly_white'
    #         )
    #         gender_ethnicity_chart = update_fig_layout(gender_ethnicity_chart)
    #         st.plotly_chart(gender_ethnicity_chart, use_container_width=True)
    #     else:
    #         st.warning("No valid data available for gender-based suicide rates.")



def display_time_trends(data, start_year, end_year):
    st.markdown('<h2 class="sub-header">Yearly Trends Analysis</h2>', unsafe_allow_html=True)
    st.markdown("""
        This section compares yearly trends for suicides and suicide attempts.
        Use the interactive options below to customize the view.
        """)

    # Define the list of month columns (all in lowercase).
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    # Build absolute paths for the monthly data files.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    suicides_month_path = os.path.join(base_dir, 'data', 'output_folder', 'Suicides - Month&Year.csv')
    attempts_month_path = os.path.join(base_dir, 'data', 'output_folder', 'Attempts - Month&Year.csv')

    try:
        suicides_month = pd.read_csv(suicides_month_path)
        attempts_month = pd.read_csv(attempts_month_path)
    except Exception as e:
        st.error(f"Error loading monthly data: {e}")
        return

    # Convert all column names to lowercase.
    suicides_month.columns = [col.lower() for col in suicides_month.columns]
    attempts_month.columns = [col.lower() for col in attempts_month.columns]

    # Filter monthly data based on the selected year range.
    suicides_month_filtered = suicides_month[
        (suicides_month['year'] >= start_year) & (suicides_month['year'] <= end_year)].copy()
    attempts_month_filtered = attempts_month[
        (attempts_month['year'] >= start_year) & (attempts_month['year'] <= end_year)].copy()

    # Compute yearly total by summing across the 12 month columns.
    suicides_month_filtered['total'] = suicides_month_filtered[months].sum(axis=1)
    attempts_month_filtered['total'] = attempts_month_filtered[months].sum(axis=1)

    # Rename the totals for clarity.
    suicides_month_filtered.rename(columns={'total': 'Suicides'}, inplace=True)
    attempts_month_filtered.rename(columns={'total': 'Attempts'}, inplace=True)

    # Aggregate yearly data.
    suicides_yearly = suicides_month_filtered[['year', 'Suicides']]
    attempts_yearly = attempts_month_filtered[['year', 'Attempts']]

    # Merge the two dataframes on the year.
    yearly_data = pd.merge(suicides_yearly, attempts_yearly, on='year')

    # Transform data to long format for Plotly.
    yearly_data_long = yearly_data.melt(id_vars='year', value_vars=['Suicides', 'Attempts'],
                                        var_name='Measure', value_name='Count')

    # Interactive option: select which measures to display.
    selected_measures = st.multiselect("Select measures to display:", options=["Suicides", "Attempts"],
                                       default=["Suicides", "Attempts"])
    filtered_data = yearly_data_long[yearly_data_long["Measure"].isin(selected_measures)]

    # Interactive option: toggle regression trendlines.
    show_trendline = st.checkbox("Show Regression Trendlines", value=True)

    if show_trendline:
        fig = px.scatter(filtered_data, x='year', y='Count', color='Measure', trendline="ols",
                         template="plotly_white",
                         title="Yearly Trends: Suicides and Suicide Attempts",
                         labels={"year": "Year", "Count": "Count"})
        fig.update_traces(marker=dict(size=8))
    else:
        fig = px.line(filtered_data, x='year', y='Count', color='Measure', markers=True,
                      template="plotly_white",
                      title="Yearly Trends: Suicides and Suicide Attempts",
                      labels={"year": "Year", "Count": "Count"})

    # Apply your custom layout updates.
    fig = update_fig_layout(fig)

    # Display the graph.
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()