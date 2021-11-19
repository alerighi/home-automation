const { GObject, St } = imports.gi;

const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;
const Soup = imports.gi.Soup;
const Mainloop = imports.mainloop;

const POLL_INTERVAL_SEC = 20
const BASE_URL = 'http://192.168.1.200:8080/light'

function setLight(light, value) {
    const soupSyncSession = new Soup.SessionSync();
    const message = Soup.Message.new('GET', BASE_URL + '?light=' + light + '&on=' + value);
    const responseCode = soupSyncSession.send_message(message);

    if (responseCode == 200) {
        return JSON.parse(message.response_body.data)
    }
}


function getLightState() {
    const soupSyncSession = new Soup.SessionSync();
    const message = Soup.Message.new('GET', BASE_URL);
    const responseCode = soupSyncSession.send_message(message);
    
    if (responseCode == 200) {
        return JSON.parse(message.response_body.data)
    }
}


const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'Home automation');        

        this.add_child(new St.Icon({
            icon_name: 'dialog-information-symbolic',
            style_class: 'system-status-icon',
        }));

        // create switches
        this.ufficio = new PopupMenu.PopupSwitchMenuItem('Ufficio', false);
        this.scale = new PopupMenu.PopupSwitchMenuItem('Scale', false);
        this.bagno = new PopupMenu.PopupSwitchMenuItem('Bagno', false);
        this.camera = new PopupMenu.PopupSwitchMenuItem('Camera', false);
        this.armadio = new PopupMenu.PopupSwitchMenuItem('Armadio', false);
        
        // connect signals
        this.ufficio.connect('activate', (params) => this.setLightState(setLight('ufficio', params.state))) 
        this.scale.connect('activate', (params) => this.setLightState(setLight('scale', params.state)))
        this.bagno.connect('activate', (params) => this.setLightState(setLight('bagno', params.state)))
        this.camera.connect('activate', (params) => this.setLightState(setLight('camera', params.state))) 
        this.armadio.connect('activate', (params) => this.setLightState(setLight('armadio', params.state))) 

        // add items
        this.menu.addMenuItem(this.ufficio);
        this.menu.addMenuItem(this.scale);
        this.menu.addMenuItem(this.bagno);
        this.menu.addMenuItem(this.camera);
        this.menu.addMenuItem(this.armadio);

        // prevent menu close
        this.menu.itemActivated = () => {}
    }


    setLightState(state) {
        this.ufficio.setToggleState(state.ufficio.state == 1)
        this.scale.setToggleState(state.scale.state == 1)
        this.bagno.setToggleState(state.bagno.state == 1)
        this.camera.setToggleState(state.camera.state == 1)
        this.armadio.setToggleState(state.armadio.state == 1)

        return true
    }
});

class Extension {
    constructor(uuid) {
        this._uuid = uuid;
    }

    enable() {
        this._indicator = new Indicator();
        Main.panel.addToStatusArea(this._uuid, this._indicator);
        
        // get initial state
        const state = getLightState();
        this._indicator.setLightState(state);

        Mainloop.timeout_add_seconds(POLL_INTERVAL_SEC, () => {
            const state = getLightState();
            this._indicator.setLightState(state);
            
            // by returning true the timeout is not canceled
            return true;
        });
    }

    disable() {
        this._indicator.destroy();
        this._indicator = null;
    }
}

function init(meta) {
    return new Extension(meta.uuid);
}

