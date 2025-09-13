import axios from 'axios';

const api = axios.create({
    baseURL : "http://localhost:8000",
});

export const startGame = async (num_players = 6, dealer_index = 0) => {
    return api.post("/hands/start", { num_players, dealer_index });
}

export const playerAction = async (action: string) => {
    return api.post(`/hands/action`, { action });
};

export const getState = async (hand_id: string) => {
    return api.get(`/hands/${hand_id}`);
};

export const getResult = async (hand_id: string) => {
    return api.get(`/hands/${hand_id}/result`);
};

// export const getHistory = async () => {
//     return api.get("/hands/");
// };