const ENDPOINT = `ws://${process.env.REACT_APP_WSHOST}:${process.env.REACT_APP_WSPORT}/`;

const getSocket = () => {
    console.log(`creating new socket connection at ${ENDPOINT}`);
    return new WebSocket(ENDPOINT);
}

export {
    getSocket,
}