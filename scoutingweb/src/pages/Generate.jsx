import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Generate.css';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { Box, Modal, Typography} from '@mui/material';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import { ArrowDropDown } from '@mui/icons-material';
import reefscapeField from '../images/reefscapefield.png';

function Generate() {
  const [matchId, setMatchId] = useState('');
  const [year, setYear] = useState('');
  const [redTeams, setRedTeams] = useState([]);
  const [blueTeams, setBlueTeams] = useState([]);
  const [popupData, setPopupData] = useState(null);
  const [teamData, setTeamData] = useState({});
  const [capabilities, setCapabilities] = useState({ red: {}, blue: {} });
  const [strategySummary, setStrategySummary] = useState('');
  const [winProbs, setWinProbs] = useState(null);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const [teamPhotos, setTeamPhotos] = useState({});
  const [imageLoading, setImageLoading] = useState(false);
  const [eventList, setEventList] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState('');
  const [matchList, setMatchList] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState('');


  useEffect(() => {
    const loadPhotos = async () => {
      const allTeams = [...redTeams, ...blueTeams];
      const photos = {};
  
      await Promise.all(
        allTeams.map(async (teamId) => {
          try {
            const res = await fetch(`http://127.0.0.1:5000/api/team-photo/${teamId}`);
            const json = await res.json();
            if (json.success) {
              photos[teamId] = json.photo_url;
            }
          } catch (err) {
            console.warn(`Failed to fetch photo for ${teamId}`, err);
          }
        })
      );
  
      setTeamPhotos(photos);
    };
  
    if (redTeams.length || blueTeams.length) {
      loadPhotos();
    }
  }, [redTeams, blueTeams]);

  const handleClick = async () => {
    const matchCode = selectedMatch || matchId;
    if (!matchCode) {
      alert('Enter match id');
    } else {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/match', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            match_code: matchCode
          })

        });

        const result = await response.json();
        if (result.success) {
          const data = result.data;
          setRedTeams(data.red.map(team => team.id));
          setBlueTeams(data.blue.map(team => team.id));
          setWinProbs(data.win_probabilities);

          const combinedData = {};
          const redSummaries = [];
          const blueSummaries = [];

          data.red.forEach(team => {
            combinedData[team.id] = {
              title: `Team ${team.id} Summary`,
              description: (team.summary || 'No summary provided.').replace(/\n/g, '<br />'),
            };
            redSummaries.push(team.summary);
          });

          data.blue.forEach(team => {
            combinedData[team.id] = {
              title: `Team ${team.id} Summary`,
              description: (team.summary || 'No summary provided.').replace(/\n/g, '<br />'),
            };
            blueSummaries.push(team.summary);
          });

          setTeamData(combinedData);
          setCapabilities(data.capabilities);

//           const stratRes = await fetch('http://localhost:5050/api/strategy-summary', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ red: redSummaries, blue: blueSummaries })
//           });

//           const stratJson = await stratRes.json();
//           if (stratJson.success) {
//             const numberedSummary = stratJson.summary
//   .replace(/Team 1/g, redTeams[0] || '')
//   .replace(/Team 2/g, redTeams[1] || '')
//   .replace(/Team 3/g, redTeams[2] || '')
//   .replace(/Team 4/g, blueTeams[0] || '')
//   .replace(/Team 5/g, blueTeams[1] || '')
//   .replace(/Team 6/g, blueTeams[2] || '');

// const formattedSummary = numberedSummary
//   .split(/[\n\r\u2022\-]/)
//   .map(s => s.trim())
//   .filter(s => s.length > 0)
//   .map(s => `• ${s}`)
//   .join("\n\n");

// setStrategySummary(formattedSummary);
  //         } else {
  //           // setStrategySummary('Unable to generate strategy summary.');
  //         }
  //       } else {
  //         // alert('Backend error: ' + result.error);
  //       }
  //     } catch (err) {
  //       // alert('Request failed: ' + err.message);
  //     }
  //   }
  // };
        };
      }
      catch{
        console.log("Error fetching match data");
      }
    }
  }

  const handleTeamClick = (teamId) => {
    const data = teamData[teamId];
    if (data) {
      const photo = teamPhotos[teamId] || null;
      console.log(`Team ${teamId} photo:`, photo);
      setImageLoading(true);
      setPopupData({ ...data, teamId });
      setOpen(true);
    } else {
      alert(`No data available for team ${teamId}`);
    }
  };

  const handleClose = () => setOpen(false);

  const handleYearSubmit = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:5000/api/events/${year}`);  // use your Flask server's URL
      const data = await res.json();
      if (data.error) {
        setEventList([{ key: '', name: 'Error' }]);
        alert("Error fetching events: " + data.error);
      } else {
        setEventList(data);  // assuming data is an array of { key, name }
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      setEventList([{ key: '', name: 'Error' }]);
    }
  };

  const handleEventSubmit = async () => {
    if (!selectedEvent) return;
  
    try {
      const res = await fetch(`http://127.0.0.1:5000/api/matches/${selectedEvent}`);
      const data = await res.json();
  
      // Check if backend returned an error object
      if (!Array.isArray(data)) {
        console.error("Error fetching matches:", data);
        alert("Failed to fetch matches. See console for details.");
        return;
      }
  
      setMatchList(data);  // This is now safe
    } catch (err) {
      console.error("Error fetching matches:", err);
      alert("Request failed");
    }
  };
  





  const CapabilityGridBox = ({ title, teams, values, alliance}) => {
    const levels = ['Level 4', 'Level 3', 'Level 2', 'Level 1'];
    const parsed = teams.map((teamId, idx) => ({
      teamId,
      set: new Set((values[idx] || '').split(', '))
    }));
    var classer = "leftboxes";
    if (alliance === 'blue') {
      classer = 'leftboxes';
    }
    else if (alliance === 'red') {
      classer = 'rightboxes';
    }


    return (
      <Box className = {classer}>
        <Typography variant="h6" fontWeight="bold">{title}</Typography>
        <div className = "capabilitycontainer">
          {parsed.map(p => (
            <div key={p.teamId} className = "capabilitybox">
              <Typography fontWeight="bold" >Team {p.teamId}</Typography>
              {levels.map(level => (
                <Typography key={level}>{p.set.has(level) ? level : '—'}</Typography>
              ))}
            </div>
          ))}
        </div>
      </Box>
    );
  };

  const ClimbGridBox = ({ title, teams, values, className }) => {
    const levels = ['Park', 'Shallow', 'Deep'];
    const parsed = teams.map((teamId, idx) => ({
      teamId,
      set: new Set((values[idx] || '').split(', '))
    }));

    return (
      <Box className={className} sx={{ mt: 2, p: 2 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>{title}</Typography>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {parsed.map(p => (
            <div key={p.teamId} style={{ flex: 1, textAlign: 'center' }}>
              <Typography fontWeight="bold" sx={{ mb: 1 }}>Team {p.teamId}</Typography>
              {levels.map(level => (
                <Typography key={level}>{p.set.has(level) ? level : '—'}</Typography>
              ))}
            </div>
          ))}
        </div>
      </Box>
    );
  };

  const AlgaeBox = ({ title, teams, values, alliance }) => {
    const parsed = values.map(val => {
      const hasProcessor = val.includes('processor');
      const hasBarge = val.includes('barge');
      if (hasProcessor && hasBarge) return 'processor and barge';
      if (hasProcessor) return 'processor';
      if (hasBarge) return 'barge';
      return 'none'; // blank if neither
    });
    var classer = "leftboxes";
    if (alliance === 'blue') {
      classer = 'leftboxes';
    }
    else if (alliance === 'red') {
      classer = 'rightboxes';
    }
  
    return (
      <Box className={classer}>
        <Typography variant="h6" fontWeight="bold">{title}</Typography>
        {teams.map((teamId, idx) => (
          <Typography key={teamId}>
            <strong>Team {teamId}:</strong> {parsed[idx]}
          </Typography>
        ))}
      </Box>
    );
  };
  const WinProbBox = ({ data }) => {
    if (data==null){
      return;
    }
    else{
    return (
      <Box className = "midbox" 
      sx={{
        background: `linear-gradient(to right, #69a2ff ${data.tba_blue}%, #fc5656 ${data.tba_blue}%)`
      }}>
        <Typography variant="h6" fontWeight="bold">Win Probability & Score Predictions</Typography>
        <Typography variant="body1" sx={{ mt: 1 }}>Event: {data.event}</Typography>
        <Typography variant="body1">Match: {data.match}</Typography>
        <Typography variant="body1">TBA Prediction — Red: {data.tba_red}%, Blue: {data.tba_blue}%</Typography>
        <Typography variant="body1">Statbotics Win Prob — Red: {data.sb_red}%, Blue: {data.sb_blue}%</Typography>
        <Typography variant="body1">Predicted EPA Score — Red: {data.epa_red}, Blue: {data.epa_blue}</Typography>

      </Box>
      /*
      <Box sx={{ mt: 4, p: 3, border: '1px solid #ccc', borderRadius: '8px', backgroundColor: '#eef9f1' }}>
        <Typography variant="h6" fontWeight="bold">Win Probability & Score Predictions</Typography>
        <Typography variant="body1" sx={{ mt: 1 }}>Event: {data.event}</Typography>
        <Typography variant="body1">Match: {data.match}</Typography>
        <Typography variant="body1">TBA Prediction — Red: {data.tba_red}%, Blue: {data.tba_blue}%</Typography>
        <Typography variant="body1">Statbotics Win Prob — Red: {data.sb_red}%, Blue: {data.sb_blue}%</Typography>
        <Typography variant="body1">Predicted EPA Score — Red: {data.epa_red}, Blue: {data.epa_blue}</Typography>
      </Box>
      */
    );
  }
  };
  const handleChange = (event) => {
    setYear(event.target.value);
  };
  return (
    <>

      {/* {strategySummary && (
        <Box sx={{ mt: 4, p: 3, border: '1px solid #ccc', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
          <Typography variant="h6" fontWeight="bold">Strategic Summary</Typography>
          <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mt: 1 }}>{strategySummary}</Typography>
        </Box>
      )} */}
      <div className="scrolling-content">
  <div className="field-container">
    <img src={reefscapeField} alt="Field" className="field-image" />

    {/* Blue alliance team overlays */}
    {blueTeams[0] && (
      <div className="blue-team-number" style={{ top: '35%', left: '2%' }}>{blueTeams[0]}</div>
    )}
    {blueTeams[1] && (
      <div className="blue-team-number" style={{ top: '50%', left: '2%' }}>{blueTeams[1]}</div>
    )}
    {blueTeams[2] && (
      <div className="blue-team-number" style={{ top: '65%', left: '2%' }}>{blueTeams[2]}</div>
    )}

    {/* Red alliance team overlays */}
    {redTeams[0] && (
      <div className="red-team-number" style={{ top: '35%', left: '97%' }}>{redTeams[0]}</div>
    )}
    {redTeams[1] && (
      <div className="red-team-number" style={{ top: '50%', left: '97%' }}>{redTeams[1]}</div>
    )}
    {redTeams[2] && (
      <div className="red-team-number" style={{ top: '65%', left: '97%' }}>{redTeams[2]}</div>
    )}
  </div>
</div>


      
      <div className="dropdown-container">
      <div className = "dropdown">
      <FormControl sx={{ mr: 2, minWidth: 120 }}>
        <InputLabel>Year</InputLabel>
        <Select value={year} onChange={handleChange}>
          {Array.from({ length: new Date().getFullYear() - 2008 + 1 }, (_, i) => 2008 + i).map((yr) => (
            <MenuItem key={yr} value={yr}>{yr}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button variant="contained" onClick={handleYearSubmit}>Get Events</Button>
      </div>

      <div className = "dropdown">
      {eventList.length > 0 && (
        <FormControl sx={{ mt: 2, minWidth: 300 }}>
          <InputLabel>Event</InputLabel>
          <Select value={selectedEvent} onChange={(e) => setSelectedEvent(e.target.value)}>
            {eventList.map((event) => (
              <MenuItem key={event.key} value={event.key}>{event.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        )}
        <Button variant="contained" sx={{ mt: 2 }} onClick={handleEventSubmit}>
          Get Matches
        </Button>
        </div>
        <div className = "dropdown">
        {matchList.length > 0 && (
          <FormControl sx={{ mt: 2, minWidth: 300 }}>
            <InputLabel>Match</InputLabel>
            <Select
              value={selectedMatch}
              onChange={(e) => {
                const selected = e.target.value;
                setSelectedMatch(selected);
                setMatchId(selected); // <-- sync dropdown with matchId input
              }}
            >
              {matchList.map((matchKey) => (
                <MenuItem key={matchKey} value={matchKey}>{matchKey}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        <Button variant="contained" onClick={handleClick}>
          Submit Selected Match
        </Button>
      </div>
      </div>
      <div className = "winprobbox">
      <WinProbBox data={winProbs}/>
      </div>

      {/* <FormControl >
        <InputLabel id="demo-simple-select-label">Year</InputLabel>
        <Select
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={year}
          label="Year"
          onChange={handleChange}
        >
          {Array.from({ length: new Date().getFullYear() - 2008 + 1 }, (_, i) => {
          const yr = 2008 + i;
          return (
            <MenuItem key={yr} value={yr}>
              {yr}
            </MenuItem>
          );
        })}
        </Select>
      </FormControl> */}

      <div className="allgroupings" style={{ marginTop: '30px' }}>
        
        <div className="groupings" style={{ display: 'flex', gap: '4rem' }  }>
          
          <div>
            <Box className="leftboxes">
              <Typography variant="h5" fontWeight="bold">Blue Alliance Teams</Typography>
              <div className = "team-buttons">
                {blueTeams.map((teamId) => (
                  <Button sx={{ border: '1px solid black', color: 'black', margin: '5px', background: 'white' }}
                    key={teamId}
                    onClick={() => handleTeamClick(teamId)}
                  >
                    {teamId}
                  </Button>
                ))}
              </div>
            </Box>
            <CapabilityGridBox title="Coral Capabilities" teams={blueTeams} values={(capabilities.blue.coral || '').split(';')} alliance= "blue"/>
            <AlgaeBox title="Algae Mechanisms" teams={blueTeams} values={(capabilities.blue.algae || '').split(';')} alliance= "blue"className="leftboxes" />
            <ClimbGridBox title="Climb Capabilities" teams={blueTeams} values={(capabilities.blue.climb || '').split(';')} className="leftboxes" />
          </div>

          <div>
            <Box className="rightboxes">
              <Typography variant="h5" fontWeight="bold">Red Alliance Teams</Typography>
              <div className = "team-buttons">
                {redTeams.map((teamId) => (
                  <Button sx={{ border: '1px solid black', color: 'black', margin: '5px', background: 'white' }}
                    key={teamId}
                    onClick={() => handleTeamClick(teamId)}
                  >
                    {teamId}
                  </Button>
                ))}
              </div>
            </Box>
            <CapabilityGridBox title="Coral Capabilities" teams={redTeams} values={(capabilities.red.coral || '').split(';')} alliance="red" className="rightboxes" />
            <AlgaeBox title="Algae Capabilities" teams={redTeams} values={(capabilities.red.algae || '').split(';')} alliance = "red" className="rightboxes" />
            <ClimbGridBox title="Climb Capabilities" teams={redTeams} values={(capabilities.red.climb || '').split(';')} className="rightboxes" />
          </div>
        </div>
      </div>

      <Modal open={open} onClose={handleClose}>
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            bgcolor: 'background.paper',
            boxShadow: 24,
            p: 4,
            borderRadius: 2,
            width: 400,
          }}
        >
          {popupData && (
  <>
    <Typography variant="h6" component="h2">
      {popupData.title}
    </Typography>

    {popupData.teamId && (
  <>
    {imageLoading && (
      <div style={{ textAlign: 'center', margin: '10px 0' }}>
        <span className="loader" />
      </div>
    )}
    <img
      src={`http://127.0.0.1:5000/api/photo-proxy/${popupData.teamId}`}
      alt="Team"
      onLoad={() => setImageLoading(false)}
      onError={(e) => {
        e.target.onerror = null;
        e.target.src = 'https://picsum.photos/200';
        setImageLoading(false);
      }}
      style={{
        width: '100%',
        maxHeight: '250px',
        objectFit: 'contain',
        borderRadius: '8px',
        marginTop: '10px',
        display: imageLoading ? 'none' : 'block'
      }}
    />
  </>
)}

              <Typography sx={{ mt: 2 }} dangerouslySetInnerHTML={{ __html: popupData.description }} />

              <Button onClick={handleClose} sx={{ mt: 3 }} variant="contained">
                Close
              </Button>
            </>
          )}
        </Box>
      </Modal>
    </>
  );
}

export default Generate;
