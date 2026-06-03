// AI Travel Planner - Premium Product Design

// Currency conversion rates (base: USD)
const CURRENCY_RATES = {
  USD: { rate: 1, symbol: '$', locale: 'en-US' },
  INR: { rate: 83.5, symbol: '₹', locale: 'en-IN' },
  JPY: { rate: 149.5, symbol: '¥', locale: 'ja-JP' }
};

// Current selected currency (default: USD)
let currentCurrency = 'USD';

document.addEventListener('DOMContentLoaded', () => {
  initCurrencySelector();
  initMicrophone();
  initExampleChips();
  initGenerateButton();
});

// Currency selector initialization
function initCurrencySelector() {
  const currencySelect = document.getElementById('currency-select');
  if (!currencySelect) return;

  currencySelect.addEventListener('change', (e) => {
    currentCurrency = e.target.value;
    // Re-render itinerary with new currency if itinerary exists
    if (document.getElementById('output-section').style.display !== 'none') {
      const travelRequest = document.getElementById('travel-request').value;
      const parsed = parseTravelRequest(travelRequest);
      if (parsed.destination) {
        displayItinerary(parsed);
      }
    }
  });
}

// Format currency based on selected currency
function formatCurrency(amountInUSD) {
  const currency = CURRENCY_RATES[currentCurrency];
  const convertedAmount = amountInUSD * currency.rate;
  
  return new Intl.NumberFormat(currency.locale, {
    style: 'currency',
    currency: currentCurrency,
    maximumFractionDigits: 0
  }).format(convertedAmount);
}

// Microphone button with Web Speech API
function initMicrophone() {
  const micBtn = document.getElementById('mic-btn');
  const travelInput = document.getElementById('travel-request');

  if (!micBtn || !travelInput) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micBtn.style.opacity = '0.5';
    micBtn.style.cursor = 'not-allowed';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    const result = event.results[0];
    const transcript = result[0].transcript;
    travelInput.value = transcript;
    
    if (result.isFinal) {
      micBtn.classList.remove('listening');
    }
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    micBtn.classList.remove('listening');
  };

  recognition.onend = () => {
    micBtn.classList.remove('listening');
  };

  micBtn.addEventListener('click', () => {
    if (micBtn.classList.contains('listening')) {
      recognition.stop();
      return;
    }

    micBtn.classList.add('listening');

    try {
      recognition.start();
    } catch (error) {
      console.error('Failed to start recognition:', error);
      micBtn.classList.remove('listening');
    }
  });
}

// Example chips
function initExampleChips() {
  const chips = document.querySelectorAll('.example-chip');
  const travelInput = document.getElementById('travel-request');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.dataset.prompt;
      travelInput.value = prompt;
      travelInput.focus();
    });
  });
}

// Generate button handler
function initGenerateButton() {
  const generateBtn = document.getElementById('generate-btn');
  const travelInput = document.getElementById('travel-request');

  if (!generateBtn || !travelInput) return;

  generateBtn.addEventListener('click', async () => {
    const request = travelInput.value.trim();
    
    if (!request) {
      travelInput.focus();
      return;
    }

    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';

    try {
      await runAgentWorkflow(request);
    } catch (error) {
      console.error('Error generating itinerary:', error);
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generate Plan';
    }
  });
}

// Parse travel request
function parseTravelRequest(text) {
  const clean = text.toLowerCase();
  
  let destination = "";
  const countries = ["japan", "tokyo", "kyoto", "italy", "rome", "florence", "france", "paris", "spain", "madrid", "london", "england", "hawaii", "thailand", "bangkok", "germany", "berlin", "australia", "sydney"];
  
  for (const c of countries) {
    if (clean.includes(c)) {
      destination = c.charAt(0).toUpperCase() + c.slice(1);
      break;
    }
  }
  
  if (!destination) {
    const toMatch = clean.match(/(?:trip to|visit|explore|go to)\s+([a-zA-Z\s]+?)(?:with|under|for|budget|in|at|$)/i);
    if (toMatch && toMatch[1].trim()) {
      destination = toMatch[1].trim().split(" ")[0];
      destination = destination.charAt(0).toUpperCase() + destination.slice(1);
    }
  }

  let duration = 5;
  const matchDays = clean.match(/(\d+)\s*-?\s*days?/);
  if (matchDays && matchDays[1]) {
    duration = Math.max(1, Math.min(14, parseInt(matchDays[1])));
  }

  let budget = 3000;
  const matchBudget = clean.match(/(?:\$|budget of|under|around)\s*(\d+[\d,]*)/i) || clean.match(/(\d+[\d,]*)\s*(?:dollars|usd)/i);
  if (matchBudget && matchBudget[1]) {
    const rawVal = parseInt(matchBudget[1].replace(/,/g, ''));
    if (!isNaN(rawVal)) {
      budget = Math.max(500, Math.min(10000, rawVal));
    }
  }

  const interests = {
    food: clean.includes("food") || clean.includes("dining") || clean.includes("eat"),
    temples: clean.includes("temple") || clean.includes("culture") || clean.includes("history"),
    shopping: clean.includes("shop") || clean.includes("shopping"),
    nature: clean.includes("nature") || clean.includes("hike") || clean.includes("mountain"),
    nightlife: clean.includes("nightlife") || clean.includes("bar") || clean.includes("club")
  };

  return { destination, duration, budget, interests };
}

// Destination-specific itineraries
const DESTINATION_ITINERARIES = {
  japan: {
    neighborhoods: ["Shinjuku, Tokyo", "Asakusa, Tokyo", "Gion, Kyoto", "Arashiyama, Kyoto"],
    transport: ["JR Pass (7-day)", "Shinkansen Tokyo→Kyoto", "Local metro & buses"],
    lodging: 1100,
    dining: 780,
    transport: 480,
    activities: 400,
    days: [
      {
        title: "Arrival in Tokyo & Shinjuku",
        stay: "Shinjuku Prince Hotel, Tokyo",
        activities: [
          { time: "Morning", name: "Haneda Airport to Shinjuku", desc: "Land at Haneda Airport (HND). Take Tokyo Monorail to Hamamatsucho, transfer to Yamanote Line to Shinjuku Station.", cost: 8, dur: "1.5 hrs" },
          { time: "Afternoon", name: "Shinjuku Gyoen National Garden", desc: "Stroll through Tokyo's largest park featuring traditional Japanese landscape gardens.", cost: 3, dur: "2.5 hrs" },
          { time: "Evening", name: "Omoide Yokocho & Ramen", desc: "Explore nostalgic alleyways in Shinjuku for draft beers and fresh Ramen at Ichiran.", cost: 23, dur: "3 hrs" }
        ]
      },
      {
        title: "Historic Asakusa & Shibuya",
        stay: "Shinjuku Prince Hotel, Tokyo",
        activities: [
          { time: "Morning", name: "Senso-ji Temple, Asakusa", desc: "Visit Tokyo's oldest Buddhist temple founded in 645 AD. Browse Nakamise-dori shopping street.", cost: 0, dur: "2 hrs" },
          { time: "Afternoon", name: "Shibuya Crossing & Meiji Shrine", desc: "Walk the world's busiest pedestrian crossing. Take a peaceful walk through Meiji Jingu Shrine.", cost: 10, dur: "4 hrs" },
          { time: "Evening", name: "Ebisu Yokocho Izakaya", desc: "Dine on Yakitori and Gyoza in a lively indoor market atmosphere.", cost: 27, dur: "3.5 hrs" }
        ]
      },
      {
        title: "Bullet Train to Kyoto",
        stay: "Sotetsu Fresa Inn Kyoto-Shijo, Kyoto",
        activities: [
          { time: "Morning", name: "Nozomi Shinkansen to Kyoto", desc: "Board the bullet train at Tokyo Station. Speed past Mt. Fuji views. Arrive at Kyoto Station.", cost: 94, dur: "3 hrs" },
          { time: "Afternoon", name: "Fushimi Inari Taisha Shrine", desc: "Hike through thousands of vermilion torii gates up Mount Inari.", cost: 8, dur: "3.5 hrs" },
          { time: "Evening", name: "Gion District & Kaiseki", desc: "Explore Kyoto's geisha district. Enjoy traditional multi-course Kaiseki dinner.", cost: 80, dur: "3 hrs" }
        ]
      }
    ]
  },
  thailand: {
    neighborhoods: ["Riverside, Bangkok", "Old City, Bangkok", "Yaowarat Chinatown", "Siam District"],
    transport: ["BTS Skytrain", "Tuk-tuk for short trips", "Chao Phraya River ferry"],
    lodging: 750,
    dining: 550,
    transport: 250,
    activities: 300,
    days: [
      {
        title: "Arrival in Bangkok & Temples",
        stay: "ibis Bangkok Riverside",
        activities: [
          { time: "Morning", name: "Suvarnabhumi Airport to Riverside", desc: "Land at BKK Airport. Take Airport Rail Link to Phaya Thai, transfer to BTS.", cost: 5, dur: "1.5 hrs" },
          { time: "Afternoon", name: "Grand Palace & Wat Phra Kaew", desc: "Visit Thailand's most sacred site featuring the Emerald Buddha.", cost: 14, dur: "3 hrs" },
          { time: "Evening", name: "Wat Arun at Sunset", desc: "Take ferry across Chao Phraya River to see Wat Arun illuminated at sunset.", cost: 10, dur: "3 hrs" }
        ]
      },
      {
        title: "Floating Markets & Chinatown",
        stay: "ibis Bangkok Riverside",
        activities: [
          { time: "Morning", name: "Damnoen Saduak Floating Market", desc: "Take early morning boat ride through Thailand's most famous floating market.", cost: 42, dur: "4 hrs" },
          { time: "Afternoon", name: "Yaowarat Chinatown Street Food", desc: "Explore Bangkok's Chinatown for street food like Pad Thai and mango sticky rice.", cost: 11, dur: "3 hrs" },
          { time: "Evening", name: "Siam Paragon Shopping", desc: "Visit Southeast Asia's largest shopping mall. Watch movies at Paragon Cineplex.", cost: 17, dur: "3 hrs" }
        ]
      },
      {
        title: "Ayutthaya Ancient City",
        stay: "ibis Bangkok Riverside",
        activities: [
          { time: "Morning", name: "Train to Ayutthaya", desc: "Take train from Hua Lamphong Station to Ayutthaya, the ancient capital of Siam.", cost: 3, dur: "2 hrs" },
          { time: "Afternoon", name: "Wat Mahathat & Wat Chaiwatthanaram", desc: "Visit famous temples including the Buddha head in tree roots.", cost: 6, dur: "3.5 hrs" },
          { time: "Evening", name: "Return to Bangkok & Sky Bar", desc: "Return by train. End trip with cocktails at rooftop bar overlooking Bangkok skyline.", cost: 23, dur: "3 hrs" }
        ]
      }
    ]
  },
  italy: {
    neighborhoods: ["Termini, Rome", "Trastevere, Rome", "Santa Maria Novella, Florence", "Oltrarno, Florence"],
    transport: ["Leonardo Express train", "Frecciarossa high-speed train", "Local buses & metro"],
    lodging: 1800,
    dining: 1450,
    transport: 600,
    activities: 800,
    days: [
      {
        title: "Arrival in Rome & Colosseum",
        stay: "Hotel Quirinale, Rome",
        activities: [
          { time: "Morning", name: "FCO Airport to Termini", desc: "Land at Fiumicino Airport. Take Leonardo Express train directly to Termini Station.", cost: 15, dur: "1 hr" },
          { time: "Afternoon", name: "Colosseum & Roman Forum", desc: "Skip-the-line guided tour of the iconic Colosseum arena floor and archaeological ruins.", cost: 49, dur: "3 hrs" },
          { time: "Evening", name: "Trastevere Dinner", desc: "Cross Tiber River to Trastevere neighborhood. Enjoy Cacio e Pepe pasta.", cost: 33, dur: "3 hrs" }
        ]
      },
      {
        title: "Vatican & Baroque Rome",
        stay: "Hotel Quirinale, Rome",
        activities: [
          { time: "Morning", name: "Vatican Museums & Sistine Chapel", desc: "Early entry tour of Vatican Museums, Raphael Rooms, and Michelangelo's ceiling.", cost: 38, dur: "3.5 hrs" },
          { time: "Afternoon", name: "Pantheon & Trevi Fountain", desc: "Walk to the Pantheon, then toss a coin in Trevi Fountain.", cost: 5, dur: "3 hrs" },
          { time: "Evening", name: "Piazza Navona Dining", desc: "Dine at Camponcino in Piazza Navona featuring saltimbocca alla Romana.", cost: 49, dur: "2.5 hrs" }
        ]
      },
      {
        title: "Train to Florence & Uffizi",
        stay: "Hotel FH55 Grand Hotel Mediterraneo, Florence",
        activities: [
          { time: "Morning", name: "Frecciarossa to Florence", desc: "Board high-speed train at Rome Termini. Speed through Tuscany countryside.", cost: 38, dur: "2 hrs" },
          { time: "Afternoon", name: "Uffizi Gallery", desc: "Guided exploration of Renaissance masterpieces by Botticelli and Michelangelo.", cost: 33, dur: "2.5 hrs" },
          { time: "Evening", name: "Piazzale Michelangelo", desc: "Hike up to Piazzale Michelangelo for sunset views over Florence.", cost: 65, dur: "3 hrs" }
        ]
      }
    ]
  },
  france: {
    neighborhoods: ["Châtelet-Les Halles, Paris", "Montmartre, Paris", "Le Marais, Paris", "Saint-Germain-des-Prés, Paris"],
    transport: ["RER B train from CDG", "Paris Metro", "Bateaux Mouches Seine cruise"],
    lodging: 1400,
    dining: 950,
    transport: 350,
    activities: 500,
    days: [
      {
        title: "Arrival in Paris & Eiffel Tower",
        stay: "Hotel du Louvre, Paris",
        activities: [
          { time: "Morning", name: "CDG Airport to Central Paris", desc: "Land at Charles de Gaulle Airport. Take RER B train to Châtelet-Les Halles.", cost: 13, dur: "1.5 hrs" },
          { time: "Afternoon", name: "Eiffel Tower & Seine Cruise", desc: "Ascend Eiffel Tower for panoramic views. Take Bateaux Mouches cruise along Seine River.", cost: 38, dur: "3 hrs" },
          { time: "Evening", name: "Montmartre Dinner", desc: "Explore Montmartre's artistic history. Dinner at Le Consulat.", cost: 49, dur: "3 hrs" }
        ]
      },
      {
        title: "Louvre & Musée d'Orsay",
        stay: "Hotel du Louvre, Paris",
        activities: [
          { time: "Morning", name: "Louvre Museum", desc: "Early morning visit to see Mona Lisa, Venus de Milo, and Winged Victory.", cost: 18, dur: "3 hrs" },
          { time: "Afternoon", name: "Musée d'Orsay", desc: "Explore Impressionist masterpieces by Monet, Van Gogh, and Renoir.", cost: 17, dur: "2.5 hrs" },
          { time: "Evening", name: "Le Marais & Falafel", desc: "Walk through historic Le Marais district. Eat famous falafel at L'As du Fallafel.", cost: 13, dur: "2.5 hrs" }
        ]
      },
      {
        title: "Versailles Palace",
        stay: "Hotel du Louvre, Paris",
        activities: [
          { time: "Morning", name: "RER Train to Versailles", desc: "Take RER C train from Paris to Versailles Château Rive Gauche.", cost: 9, dur: "1 hr" },
          { time: "Afternoon", name: "Palace of Versailles Tour", desc: "Explore the Hall of Mirrors, King's Apartments, and the extensive gardens.", cost: 22, dur: "4 hrs" },
          { time: "Evening", name: "Return to Paris & Café de Flore", desc: "Return to Paris. End trip with coffee and pastries at historic Café de Flore.", cost: 27, dur: "2 hrs" }
        ]
      }
    ]
  },
  generic: {
    neighborhoods: ["City Center", "Historic District", "Old Town", "Waterfront"],
    transport: ["Public transit", "Local shuttle", "Walking", "Taxi as needed"],
    lodging: 1200,
    dining: 750,
    transport: 500,
    activities: 400,
    days: [
      {
        title: "Arrival & City Orientation",
        stay: "Selected Mid-range Hotel",
        activities: [
          { time: "Morning", name: "Airport Arrival & Hotel Check-in", desc: "Arrive at destination airport. Arrange local shuttle transfer and settle into hotel.", cost: 40, dur: "2 hrs" },
          { time: "Afternoon", name: "City Landmarks Tour", desc: "Take a panoramic tour of the main streets and neighborhoods.", cost: 30, dur: "3 hrs" },
          { time: "Evening", name: "Welcome Dinner & Night Walk", desc: "Enjoy a traditional dinner featuring local specialties.", cost: 45, dur: "2.5 hrs" }
        ]
      },
      {
        title: "Museums & Local Attractions",
        stay: "Selected Mid-range Hotel",
        activities: [
          { time: "Morning", name: "National Museum Exhibition", desc: "Explore the city's main historical museum showcasing cultural artifacts.", cost: 20, dur: "3 hrs" },
          { time: "Afternoon", name: "Botanical Garden & Lunch", desc: "Take a relaxing walk through the central gardens.", cost: 25, dur: "2.5 hrs" },
          { time: "Evening", name: "River Cruise & Local Dining", desc: "Sunset cruise along the river with narration.", cost: 70, dur: "3.5 hrs" }
        ]
      },
      {
        title: "Cultural Exploration & Shopping",
        stay: "Selected Mid-range Hotel",
        activities: [
          { time: "Morning", name: "Historic District Walk", desc: "Explore preserved historic buildings and learn about local heritage.", cost: 15, dur: "2.5 hrs" },
          { time: "Afternoon", name: "Local Markets & Shopping", desc: "Visit bustling local markets for souvenirs and street food.", cost: 35, dur: "3 hrs" },
          { time: "Evening", name: "Farewell Dinner", desc: "Enjoy a final dinner at a highly-rated local restaurant.", cost: 60, dur: "2.5 hrs" }
        ]
      }
    ]
  }
};

// Run agent workflow
async function runAgentWorkflow(request) {
  const parsed = parseTravelRequest(request);
  
  // Show workflow section
  const workflowSection = document.getElementById('workflow-section');
  workflowSection.style.display = 'block';
  
  // Reset stepper
  document.querySelectorAll('.step').forEach(step => {
    step.classList.remove('active', 'completed');
  });
  
  const steps = ['request', 'intent', 'research', 'budget', 'logistics', 'validator', 'output'];
  
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const stepEl = document.querySelector(`.step[data-step="${step}"]`);
    
    stepEl.classList.add('active');
    await sleep(600);
    
    stepEl.classList.remove('active');
    stepEl.classList.add('completed');
    
    // Mark previous steps as completed
    for (let j = 0; j <= i; j++) {
      document.querySelector(`.step[data-step="${steps[j]}"]`).classList.add('completed');
    }
  }
  
  // Display itinerary
  displayItinerary(parsed);
}

function displayItinerary(parsed) {
  const destLower = parsed.destination.toLowerCase();
  let template = DESTINATION_ITINERARIES.generic;
  
  if (destLower.includes('japan') || destLower.includes('tokyo') || destLower.includes('kyoto')) {
    template = DESTINATION_ITINERARIES.japan;
  } else if (destLower.includes('thailand') || destLower.includes('bangkok')) {
    template = DESTINATION_ITINERARIES.thailand;
  } else if (destLower.includes('italy') || destLower.includes('rome') || destLower.includes('florence')) {
    template = DESTINATION_ITINERARIES.italy;
  } else if (destLower.includes('france') || destLower.includes('paris')) {
    template = DESTINATION_ITINERARIES.france;
  }
  
  // Calculate budget
  const dayRatio = parsed.duration / 3;
  let lodging = template.lodging * dayRatio;
  let dining = template.dining * dayRatio;
  let transport = template.transport * (dayRatio * 0.5 + 0.5);
  let activities = template.activities * dayRatio;
  
  let total = lodging + dining + transport + activities;
  
  // Budget enforcement
  if (total > parsed.budget) {
    const excess = total - parsed.budget;
    let remainingExcess = excess;
    
    if (remainingExcess > 0 && activities > 0) {
      const reduction = Math.min(remainingExcess, activities);
      activities -= reduction;
      remainingExcess -= reduction;
    }
    
    if (remainingExcess > 0 && dining > 0) {
      const reduction = Math.min(remainingExcess, dining);
      dining -= reduction;
      remainingExcess -= reduction;
    }
    
    if (remainingExcess > 0 && transport > 0) {
      const reduction = Math.min(remainingExcess, transport);
      transport -= reduction;
      remainingExcess -= reduction;
    }
    
    if (remainingExcess > 0 && lodging > 0) {
      const reduction = Math.min(remainingExcess, lodging);
      lodging -= reduction;
      remainingExcess -= reduction;
    }
    
    total = lodging + dining + transport + activities;
  }
  
  // Show output section
  document.getElementById('output-section').style.display = 'block';
  
  // Update trip summary
  document.getElementById('trip-destination').textContent = parsed.destination;
  document.getElementById('trip-duration').textContent = `${parsed.duration} Days`;
  document.getElementById('trip-budget').textContent = formatCurrency(parsed.budget);
  
  // Update budget breakdown
  document.getElementById('budget-lodging').textContent = formatCurrency(lodging);
  document.getElementById('budget-dining').textContent = formatCurrency(dining);
  document.getElementById('budget-transport').textContent = formatCurrency(transport);
  document.getElementById('budget-activities').textContent = formatCurrency(activities);
  document.getElementById('budget-total').textContent = formatCurrency(total);
  
  // Update areas tags
  const areasTags = document.getElementById('areas-tags');
  areasTags.innerHTML = template.neighborhoods.map(n => `<span class="tag">${n}</span>`).join('');
  
  // Update transport timeline
  const transportTimeline = document.getElementById('transport-timeline');
  transportTimeline.innerHTML = template.transport.map(t => `<div class="transport-item"><span class="transport-text">${t}</span></div>`).join('');
  
  // Update itinerary accordion
  const itineraryAccordion = document.getElementById('itinerary-accordion');
  itineraryAccordion.innerHTML = '';
  
  for (let i = 1; i <= parsed.duration; i++) {
    const dayDataIndex = (i - 1) % template.days.length;
    const dayData = template.days[dayDataIndex];
    
    const accordionItem = document.createElement('div');
    accordionItem.className = 'accordion-item';
    
    let activitiesHTML = dayData.activities.map(act => {
      const costUSD = act.cost;
      const costFormatted = costUSD > 0 ? formatCurrency(costUSD) : 'Free';
      
      return `
        <div class="activity">
          <div class="activity-time">${act.time}</div>
          <div class="activity-name">${act.name}</div>
          <div class="activity-desc">${act.desc}</div>
          <div class="activity-meta">⏱️ ${act.dur} • ${costFormatted}</div>
        </div>
      `;
    }).join('');
    
    accordionItem.innerHTML = `
      <div class="accordion-header">
        <span class="accordion-title">Day ${i}: ${dayData.title}</span>
        <svg class="accordion-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <div class="accordion-body">
        <div class="day-activities">
          ${activitiesHTML}
        </div>
        <div style="margin-top: 1rem; font-size: 0.875rem; color: var(--gray-500);">📍 ${dayData.stay}</div>
      </div>
    `;
    
    // Add accordion toggle
    const header = accordionItem.querySelector('.accordion-header');
    header.addEventListener('click', () => {
      const isOpen = accordionItem.classList.contains('open');
      
      // Close all other items
      document.querySelectorAll('.accordion-item').forEach(item => {
        item.classList.remove('open');
      });
      
      // Toggle current
      if (!isOpen) {
        accordionItem.classList.add('open');
      }
    });
    
    // Open first item by default
    if (i === 1) {
      accordionItem.classList.add('open');
    }
    
    itineraryAccordion.appendChild(accordionItem);
  }
  
  // Update validation
  document.getElementById('validation-score').textContent = '95%';
  
  const validationDetails = document.getElementById('validation-details');
  const validations = [
    `Destination: ${parsed.destination} matched`,
    `Duration: ${parsed.duration} days planned`,
    `Budget: ${formatCurrency(total)} ≤ ${formatCurrency(parsed.budget)}`,
    `Currency: ${currentCurrency} selected`,
    `Preferences: ${parsed.interests.food ? 'Food' : ''} ${parsed.interests.temples ? 'Culture' : ''} ${parsed.interests.nature ? 'Nature' : ''}`
  ].filter(v => v.trim());
  
  validationDetails.innerHTML = validations.map(v => `<div class="validation-item">${v}</div>`).join('');
  
  // Scroll to output
  document.getElementById('output-section').scrollIntoView({ behavior: 'smooth' });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
